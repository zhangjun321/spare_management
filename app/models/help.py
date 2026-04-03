# -*- coding: utf-8 -*-
"""
帮助文档模型
"""

from datetime import datetime
from app.extensions import db


class HelpCategory(db.Model):
    """帮助文档分类表"""
    
    __tablename__ = 'help_category'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类ID')
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    code = db.Column(db.String(100), unique=True, nullable=False, index=True, comment='分类编码')
    description = db.Column(db.String(500), nullable=True, comment='分类描述')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')
    icon = db.Column(db.String(100), nullable=True, comment='图标')
    status = db.Column(db.Boolean, nullable=False, default=True, comment='状态：0-禁用，1-启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    documents = db.relationship('HelpDocument', foreign_keys='HelpDocument.category_id', 
                                backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<HelpCategory {self.name}>'


class HelpDocument(db.Model):
    """帮助文档表"""
    
    __tablename__ = 'help_document'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='文档ID')
    category_id = db.Column(db.Integer, db.ForeignKey('help_category.id'), nullable=False, index=True, comment='分类ID')
    title = db.Column(db.String(200), nullable=False, index=True, comment='文档标题')
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True, comment='文档别名（URL友好）')
    content = db.Column(db.Text, nullable=False, comment='文档内容（Markdown）')
    summary = db.Column(db.String(500), nullable=True, comment='文档摘要')
    tags = db.Column(db.String(500), nullable=True, comment='标签（逗号分隔）')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True, comment='作者ID')
    view_count = db.Column(db.Integer, nullable=False, default=0, comment='浏览次数')
    is_published = db.Column(db.Boolean, nullable=False, default=False, comment='是否发布')
    is_featured = db.Column(db.Boolean, nullable=False, default=False, comment='是否精选')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    author = db.relationship('User', foreign_keys=[author_id])
    
    def __repr__(self):
        return f'<HelpDocument {self.title}>'
    
    def get_tags_list(self):
        """获取标签列表"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_view_count(self):
        """增加浏览次数"""
        self.view_count += 1
        db.session.commit()


def init_help_data():
    """初始化帮助文档数据"""
    # 检查是否已初始化
    if HelpCategory.query.count() > 0:
        return
    
    # 创建默认分类
    categories = [
        {
            'name': '快速开始',
            'code': 'quick_start',
            'description': '新用户入门指南',
            'icon': 'fa-rocket',
            'sort_order': 1
        },
        {
            'name': '备件管理',
            'code': 'spare_parts',
            'description': '备件管理相关文档',
            'icon': 'fa-box',
            'sort_order': 2
        },
        {
            'name': '仓库管理',
            'code': 'warehouses',
            'description': '仓库管理相关文档',
            'icon': 'fa-warehouse',
            'sort_order': 3
        },
        {
            'name': '系统管理',
            'code': 'system',
            'description': '系统管理相关文档',
            'icon': 'fa-cog',
            'sort_order': 4
        },
        {
            'name': '常见问题',
            'code': 'faq',
            'description': '常见问题解答',
            'icon': 'fa-question-circle',
            'sort_order': 5
        }
    ]
    
    category_objects = []
    for cat_data in categories:
        cat = HelpCategory(**cat_data)
        category_objects.append(cat)
        db.session.add(cat)
    
    db.session.flush()
    
    # 创建默认文档
    documents = [
        {
            'category_id': category_objects[0].id,
            'title': '系统登录指南',
            'slug': 'login-guide',
            'content': '''# 系统登录指南

## 登录步骤

1. 打开浏览器，访问系统地址
2. 输入用户名和密码
3. 点击"登录"按钮

## 忘记密码

如果忘记密码，请联系系统管理员重置密码。

## 安全建议

- 定期更换密码
- 不要在公共设备上保存密码
- 登录后及时退出
''',
            'summary': '如何登录系统的详细指南',
            'tags': '登录,安全,入门',
            'is_published': True,
            'is_featured': True,
            'sort_order': 1
        },
        {
            'category_id': category_objects[0].id,
            'title': '界面导航说明',
            'slug': 'navigation-guide',
            'content': '''# 界面导航说明

## 顶部导航栏

- 左侧：系统Logo和名称
- 右侧：用户信息、通知、设置

## 左侧菜单

- 仪表盘：系统概览
- 备件管理：备件和批次管理
- 仓库管理：仓库和库存管理
- 交易管理：出入库记录
- 设备管理：设备信息
- 维修管理：维修工单
- 采购管理：采购流程
- 报表统计：数据报表
- 系统管理：系统设置
''',
            'summary': '系统界面布局和导航说明',
            'tags': '导航,界面,入门',
            'is_published': True,
            'sort_order': 2
        },
        {
            'category_id': category_objects[1].id,
            'title': '如何添加备件',
            'slug': 'add-spare-part',
            'content': '''# 如何添加备件

## 操作步骤

1. 进入"备件管理"页面
2. 点击"新建备件"按钮
3. 填写备件信息：
   - 备件名称
   - 备件编码
   - 分类
   - 规格型号
   - 单位
   - 安全库存
4. 点击"保存"按钮

## 注意事项

- 备件编码必须唯一
- 建议填写完整的规格信息
- 安全库存用于库存预警
''',
            'summary': '添加新备件的详细步骤',
            'tags': '备件,添加,操作',
            'is_published': True,
            'is_featured': True,
            'sort_order': 1
        },
        {
            'category_id': category_objects[4].id,
            'title': '如何重置密码',
            'slug': 'reset-password',
            'content': '''# 如何重置密码

## 管理员重置密码

1. 登录管理员账号
2. 进入用户管理
3. 找到需要重置密码的用户
4. 点击"重置密码"
5. 设置新密码

## 用户自行修改

1. 登录系统
2. 进入个人设置
3. 点击"修改密码"
4. 输入旧密码和新密码
5. 确认保存
''',
            'summary': '密码重置的方法',
            'tags': '密码,安全,FAQ',
            'is_published': True,
            'sort_order': 1
        }
    ]
    
    for doc_data in documents:
        doc = HelpDocument(**doc_data)
        db.session.add(doc)
    
    db.session.commit()
