# -*- coding: utf-8 -*-
"""
帮助文档管理路由
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.help import HelpCategory, HelpDocument, init_help_data
from app.utils.decorators import permission_required
import re

help_bp = Blueprint('help', __name__, template_folder='../templates/help')


def slugify(text):
    """生成URL友好的别名"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    text = text.strip('-_')
    return text


@help_bp.route('/')
@login_required
def help_index():
    """帮助文档首页"""
    try:
        init_help_data()
    except Exception as e:
        pass
    
    # 获取精选文档
    featured_docs = HelpDocument.query.filter_by(
        is_published=True, is_featured=True
    ).order_by(HelpDocument.sort_order, HelpDocument.created_at.desc()).limit(6).all()
    
    # 获取所有分类
    categories = HelpCategory.query.filter_by(status=True).order_by(
        HelpCategory.sort_order, HelpCategory.created_at
    ).all()
    
    return render_template('help/index.html', 
                         featured_docs=featured_docs, 
                         categories=categories)


@help_bp.route('/doc/<slug>')
@login_required
def help_detail(slug):
    """帮助文档详情页"""
    doc = HelpDocument.query.filter_by(slug=slug, is_published=True).first_or_404()
    doc.increment_view_count()
    
    # 获取相关文档（同分类）
    related_docs = HelpDocument.query.filter(
        HelpDocument.category_id == doc.category_id,
        HelpDocument.id != doc.id,
        HelpDocument.is_published == True
    ).order_by(HelpDocument.view_count.desc()).limit(5).all()
    
    return render_template('help/detail.html', doc=doc, related_docs=related_docs)


@help_bp.route('/category/<code>')
@login_required
def help_category(code):
    """按分类查看文档"""
    category = HelpCategory.query.filter_by(code=code, status=True).first_or_404()
    docs = HelpDocument.query.filter_by(
        category_id=category.id, is_published=True
    ).order_by(HelpDocument.sort_order, HelpDocument.created_at.desc()).all()
    
    categories = HelpCategory.query.filter_by(status=True).order_by(
        HelpCategory.sort_order, HelpCategory.created_at
    ).all()
    
    return render_template('help/category.html', 
                         category=category, docs=docs, categories=categories)


@help_bp.route('/search')
@login_required
def help_search():
    """搜索文档"""
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        docs = []
    else:
        docs = HelpDocument.query.filter(
            HelpDocument.is_published == True,
            (HelpDocument.title.contains(keyword) | 
             HelpDocument.content.contains(keyword) |
             HelpDocument.tags.contains(keyword))
        ).order_by(HelpDocument.view_count.desc()).limit(20).all()
    
    categories = HelpCategory.query.filter_by(status=True).order_by(
        HelpCategory.sort_order, HelpCategory.created_at
    ).all()
    
    return render_template('help/search.html', 
                         docs=docs, keyword=keyword, categories=categories)


@help_bp.route('/manage')
@login_required
@permission_required('system', 'read')
def help_manage():
    """帮助文档管理首页"""
    return render_template('help/manage.html')


@help_bp.route('/api/categories')
@login_required
@permission_required('system', 'read')
def get_categories():
    """获取分类列表"""
    try:
        categories = HelpCategory.query.order_by(
            HelpCategory.sort_order, HelpCategory.created_at.desc()
        ).all()
        
        data = []
        for cat in categories:
            doc_count = cat.documents.count() if cat.documents else 0
            data.append({
                'id': cat.id,
                'name': cat.name,
                'code': cat.code,
                'description': cat.description,
                'icon': cat.icon,
                'status': cat.status,
                'sort_order': cat.sort_order,
                'doc_count': doc_count,
                'created_at': cat.created_at.strftime('%Y-%m-%d %H:%M:%S') if cat.created_at else None
            })
        
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@help_bp.route('/api/documents')
@login_required
@permission_required('system', 'read')
def get_documents():
    """获取文档列表"""
    try:
        category_id = request.args.get('category_id', type=int)
        query = HelpDocument.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        docs = query.order_by(HelpDocument.sort_order, HelpDocument.created_at.desc()).all()
        
        data = []
        for doc in docs:
            data.append({
                'id': doc.id,
                'category_id': doc.category_id,
                'category_name': doc.category.name if doc.category else '',
                'title': doc.title,
                'slug': doc.slug,
                'summary': doc.summary,
                'view_count': doc.view_count,
                'is_published': doc.is_published,
                'is_featured': doc.is_featured,
                'sort_order': doc.sort_order,
                'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else None
            })
        
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@help_bp.route('/api/documents/<int:doc_id>')
@login_required
@permission_required('system', 'read')
def get_document(doc_id):
    """获取单个文档详情"""
    try:
        doc = HelpDocument.query.get_or_404(doc_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': doc.id,
                'category_id': doc.category_id,
                'title': doc.title,
                'slug': doc.slug,
                'content': doc.content,
                'summary': doc.summary,
                'tags': doc.tags,
                'is_published': doc.is_published,
                'is_featured': doc.is_featured,
                'sort_order': doc.sort_order
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@help_bp.route('/api/documents/create', methods=['POST'])
@login_required
@permission_required('system', 'write')
def create_document():
    """创建文档"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'category_id' not in data:
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        # 生成别名
        title = data['title']
        base_slug = slugify(title)
        slug = base_slug
        
        # 检查别名是否已存在
        counter = 1
        while HelpDocument.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        doc = HelpDocument(
            category_id=data['category_id'],
            title=title,
            slug=slug,
            content=data.get('content', ''),
            summary=data.get('summary', ''),
            tags=data.get('tags', ''),
            author_id=current_user.id,
            is_published=data.get('is_published', False),
            is_featured=data.get('is_featured', False),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(doc)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '文档创建成功',
            'data': {'id': doc.id, 'slug': doc.slug}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@help_bp.route('/api/documents/<int:doc_id>/update', methods=['PUT'])
@login_required
@permission_required('system', 'write')
def update_document(doc_id):
    """更新文档"""
    try:
        doc = HelpDocument.query.get_or_404(doc_id)
        data = request.get_json()
        
        if 'title' in data:
            doc.title = data['title']
            # 如果修改了标题，重新生成别名
            if doc.title != data.get('original_title', doc.title):
                base_slug = slugify(data['title'])
                slug = base_slug
                counter = 1
                while HelpDocument.query.filter(
                    HelpDocument.slug == slug, HelpDocument.id != doc_id
                ).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                doc.slug = slug
        
        if 'category_id' in data:
            doc.category_id = data['category_id']
        if 'content' in data:
            doc.content = data['content']
        if 'summary' in data:
            doc.summary = data['summary']
        if 'tags' in data:
            doc.tags = data['tags']
        if 'is_published' in data:
            doc.is_published = data['is_published']
        if 'is_featured' in data:
            doc.is_featured = data['is_featured']
        if 'sort_order' in data:
            doc.sort_order = data['sort_order']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '文档更新成功',
            'data': {'slug': doc.slug}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@help_bp.route('/api/documents/<int:doc_id>/delete', methods=['DELETE'])
@login_required
@permission_required('system', 'write')
def delete_document(doc_id):
    """删除文档"""
    try:
        doc = HelpDocument.query.get_or_404(doc_id)
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '文档删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
