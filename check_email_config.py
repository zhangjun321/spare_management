from app import create_app
from app.extensions import db
from app.models.system import UserEmailConfig
from app.models.user import User

# 创建应用实例
app = create_app()

with app.app_context():
    # 获取系统管理员用户
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        print(f"Admin user found: {admin.username}")
        
        # 查找该用户的邮箱配置
        config = UserEmailConfig.query.filter_by(user_id=admin.id).first()
        if config:
            print("Email config found:")
            print(f"  SMTP Server: {config.smtp_server}")
            print(f"  Username: {config.username}")
            print(f"  Password length: {len(config.password) if config.password else 0}")
            print(f"  Sender Email: {config.sender_email}")
        else:
            print("No email config found for admin user")
    else:
        print("No admin user found")
    
    # 查找所有邮箱配置
    all_configs = UserEmailConfig.query.all()
    print(f"\nTotal email configs: {len(all_configs)}")
    for i, cfg in enumerate(all_configs):
        print(f"Config {i+1}:")
        print(f"  User ID: {cfg.user_id}")
        print(f"  SMTP Server: {cfg.smtp_server}")
        print(f"  Username: {cfg.username}")
        print(f"  Password length: {len(cfg.password) if cfg.password else 0}")