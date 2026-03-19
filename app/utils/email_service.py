"""
邮件发送服务
"""

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from app.models.system import EmailConfig
from app.extensions import db

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""
    
    def __init__(self):
        self.config = None
    
    def get_config(self, user_id=None):
        """获取邮件配置
        
        Args:
            user_id: 用户 ID，如果提供则优先使用用户邮箱配置
        
        Returns:
            邮件配置对象
        """
        if self.config is None:
            # 如果提供了 user_id，优先使用用户邮箱配置
            if user_id:
                from app.models.system import UserEmailConfig
                self.config = UserEmailConfig.query.filter_by(user_id=user_id, is_active=True).first()
            
            # 如果没有用户配置，使用系统默认配置
            if not self.config:
                self.config = EmailConfig.query.filter_by(is_active=True).first()
        
        return self.config
    
    def send_email(self, to_email, to_name, subject, html_content, text_content=None, user_id=None):
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            to_name: 收件人名称
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容（可选）
            user_id: 用户 ID（可选，用于获取用户邮箱配置）
        
        Returns:
            bool: 发送是否成功
        """
        config = self.get_config(user_id)
        
        if not config:
            logger.error("未找到有效的邮件配置")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            # 正确编码发件人信息
            if config.sender_name:
                msg['From'] = Header(f"{config.sender_name}", 'utf-8').encode() + f" <{config.sender_email}>"
            else:
                msg['From'] = config.sender_email
            msg['To'] = f"{to_name} <{to_email}>"
            
            # 添加纯文本版本
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加 HTML 版本
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 连接 SMTP 服务器并发送邮件
            if config.use_tls:
                server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port)
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            
            server.login(config.username, config.password)
            server.sendmail(config.sender_email, [to_email], msg.as_string())
            server.quit()
            
            logger.info(f"邮件发送成功：{to_email}, 主题：{subject}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败：{to_email}, 错误：{str(e)}")
            return False
    
    def send_stock_alert(self, user, spare_part, user_id=None):
        """
        发送库存预警邮件
        
        Args:
            user: 用户对象
            spare_part: 备件对象
            user_id: 用户 ID（可选，用于获取用户邮箱配置）
        """
        subject = f"库存预警：{spare_part.part_code} - {spare_part.name}"
        
        # 库存状态映射
        status_map = {
            'low': '低库存',
            'out': '缺货',
            'overstocked': '超储'
        }
        
        status = status_map.get(spare_part.stock_status, '未知')
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc3545;">库存预警通知</h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>备件代码：</strong>{spare_part.part_code}</p>
                    <p><strong>备件名称：</strong>{spare_part.name}</p>
                    <p><strong>规格型号：</strong>{spare_part.specification or '-'}</p>
                    <p><strong>库存状态：</strong><span style="color: #dc3545;">{status}</span></p>
                    <p><strong>当前库存：</strong>{spare_part.current_stock}</p>
                    <p><strong>最低库存：</strong>{spare_part.min_stock}</p>
                    <p><strong>最高库存：</strong>{spare_part.max_stock or '-'}</p>
                    <p><strong>存放位置：</strong>{spare_part.location or '-'}</p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">
                    <p style="margin: 0;"><strong>提示：</strong>请及时处理库存预警，确保库存充足或避免积压。</p>
                </div>
                
                <p style="margin-top: 20px; color: #6c757d;">
                    此邮件由系统自动发送，请勿回复。<br>
                    发送时间：{spare_part.updated_at.strftime('%Y-%m-%d %H:%M:%S') if spare_part.updated_at else '-'}
                </p>
            </div>
        </body>
        </html>
        """
        
        to_name = user.real_name or user.username
        return self.send_email(user.email, to_name, subject, html_content, user_id=user_id)
    
    def test_connection(self, send_test_email=False):
        """
        测试邮件连接
        
        Args:
            send_test_email: 是否发送测试邮件
        
        Returns:
            tuple: (success: bool, message: str)
        """
        config = self.get_config()
        
        if not config:
            return False, "未找到有效的邮件配置"
        
        try:
            logger.info(f"开始测试邮件连接：{config.smtp_server}:{config.smtp_port}")
            
            # 设置超时时间为 30 秒
            if config.use_tls:
                server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=30)
            
            logger.info("SMTP 连接成功")
            
            # 登录
            server.login(config.username, config.password)
            logger.info("登录成功")
            
            # 如果需要发送测试邮件
            if send_test_email:
                test_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #28a745;">邮件测试成功</h2>
                        
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p>恭喜！邮件服务器配置正确，可以正常发送邮件。</p>
                        </div>
                        
                        <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745;">
                            <p style="margin: 0;"><strong>配置信息：</strong></p>
                            <p>SMTP 服务器：{config.smtp_server}:{config.smtp_port}</p>
                            <p>发件人：{config.sender_name} &lt;{config.sender_email}&gt;</p>
                        </div>
                        
                        <p style="margin-top: 20px; color: #6c757d;">
                            此邮件为系统自动发送的测试邮件。<br>
                            发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
                </html>
                """
                
                msg = MIMEMultipart('alternative')
                msg['Subject'] = Header('备件管理系统 - 邮件测试', 'utf-8')
                # 正确编码发件人信息
                if config.sender_name:
                    msg['From'] = Header(f"{config.sender_name}", 'utf-8').encode() + f" <{config.sender_email}>"
                else:
                    msg['From'] = config.sender_email
                msg['To'] = config.sender_email
                
                html_part = MIMEText(test_html, 'html', 'utf-8')
                msg.attach(html_part)
                
                logger.info("开始发送邮件...")
                server.sendmail(config.sender_email, [config.sender_email], msg.as_string())
                logger.info("邮件发送成功")
                server.quit()
                
                return True, "测试邮件已发送，请检查收件箱（包括垃圾邮件文件夹）"
            else:
                server.quit()
                return True, "邮件服务器连接成功"
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP 认证失败")
            return False, "SMTP 认证失败，请检查用户名和密码（或授权码）"
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP 连接失败：{str(e)}")
            return False, f"无法连接到 SMTP 服务器：{config.smtp_server}:{config.smtp_port}"
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"服务器断开连接：{str(e)}")
            return False, "邮件服务器意外断开连接，请检查网络或稍后重试"
        except Exception as e:
            logger.error(f"测试失败：{str(e)}", exc_info=True)
            return False, f"测试失败：{str(e)}"


# 全局邮件服务实例
email_service = EmailService()
