        return jsonify({
            'success': False,
            'message': f'上传失败：{str(e)}'
        }), 500


# 豁免自动上传 API 的 CSRF 保护
csrf.exempt(auto_upload_image_by_code)
