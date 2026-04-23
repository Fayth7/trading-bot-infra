"""
Monitoring, logging, and reporting
"""

import smtplib
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

from config.settings import EmailConfig, TradingConfig, FileConfig
from bot.utils import get_timestamp_eat, format_currency


class Monitor:
    """Handle logging, alerts, and performance reporting"""
    
    def __init__(self, exchange, trade_manager):
        self.exchange = exchange
        self.trades = trade_manager
    
    def log_trade(self, action, price, quantity, trade_id, profit_loss=None):
        """Log trade to file and Excel"""
        timestamp = get_timestamp_eat().strftime("%Y-%m-%d %H:%M:%S")
        
        # Text log
        log_entry = f"{timestamp} | {action} | ID: {trade_id} | Price: ${price:.2f} | Qty: {quantity:.4f}"
        if profit_loss:
            log_entry += f" | P/L: ${profit_loss:.2f}"
        
        with open(FileConfig.LOG_FILE, 'a') as f:
            f.write(log_entry + "\n")
        
        print(log_entry)
        
        # Excel log
        try:
            trade_data = {
                "Trade ID": [trade_id],
                "Timestamp": [timestamp],
                "Action": [action],
                "Price": [price],
                "Quantity": [quantity],
                "Profit/Loss": [profit_loss] if profit_loss else [None]
            }
            
            new_df = pd.DataFrame(trade_data)
            
            if os.path.exists(FileConfig.EXCEL_FILE):
                existing_df = pd.read_excel(FileConfig.EXCEL_FILE)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_excel(FileConfig.EXCEL_FILE, index=False)
            else:
                new_df.to_excel(FileConfig.EXCEL_FILE, index=False)
                
        except Exception as e:
            print(f"Excel log error: {e}")
    
    def send_email(self, subject, body, attachment_path=None):
        """Send email alert with optional attachment"""
        if not EmailConfig.EMAIL_ADDRESS:
            print("Email not configured - skipping")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = EmailConfig.EMAIL_ADDRESS
            msg['To'] = ", ".join(EmailConfig.RECIPIENT_EMAILS)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
                    msg.attach(part)
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EmailConfig.EMAIL_ADDRESS, EmailConfig.EMAIL_PASSWORD)
                server.send_message(msg)
            
            print(" Email sent")
            
        except Exception as e:
            print(f"Email failed: {e}")
    
    def generate_performance_report(self):
        """Generate performance report"""
        try:
            # Get current balances
            balances = self.exchange.fetch_balance()
            ticker = self.exchange.fetch_ticker(TradingConfig.TRADING_PAIR)
            current_price = ticker['last']
            
            spot_usdt = balances['USDT']['free']
            spot_eth = balances['ETH']['free']
            
            # Calculate portfolio value
            eth_value = spot_eth * current_price
            total_value = spot_usdt + eth_value
            
            # Calculate returns
            net_invested = max(0, self.trades.total_invested - self.trades.total_withdrawn)
            net_profit = total_value - net_invested
            roi = (net_profit / net_invested * 100) if net_invested > 0 else 0
            
            report = f"""
 TRADING BOT REPORT
═══════════════════════════════════════════
 {get_timestamp_eat().strftime('%Y-%m-%d %H:%M:%S')}

 PORTFOLIO
   Total Value: ${total_value:,.2f}
   USDT: ${spot_usdt:,.2f}
   ETH: {spot_eth:.4f} (${eth_value:,.2f})

 PERFORMANCE
   Net Invested: ${net_invested:,.2f}
   Net Profit: ${net_profit:+,.2f}
   ROI: {roi:+.2f}%

 TRADING STATS
   Active Trades: {len(self.trades.active_trades)}
   Total Earnings: ${self.trades.total_earnings:,.2f}
   Reinvested: ${self.trades.total_profits_reinvested:,.2f}
   
 Current Price: ${current_price:.2f}
═══════════════════════════════════════════
"""
            return report
            
        except Exception as e:
            return f"Report generation failed: {e}"
    
    def health_check(self):
        """Run health checks"""
        print("\n Health Check")
        
        issues = []
        
        # Check balance sufficiency
        try:
            balances = self.exchange.fetch_balance()
            if balances['USDT']['free'] < 10:
                issues.append("Low USDT balance (< $10)")
        except Exception as e:
            issues.append(f"Balance check failed: {e}")
        
        # Check active trades file
        if not os.path.exists(FileConfig.ACTIVE_TRADES_FILE):
            issues.append("Active trades file missing")
        
        # Report
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"   - {issue}")
            self.send_email(" Bot Health Alert", "\n".join(issues))
        else:
            print(" All systems normal")
    
    def send_status_report(self):
        """Send periodic status update"""
        report = self.generate_performance_report()
        print(report)
    
    def send_weekly_report(self):
        """Send weekly performance report"""
        report = self.generate_performance_report()
        self.send_email(
            subject=f" Weekly Trading Report - {get_timestamp_eat().strftime('%Y-%m-%d')}",
            body=report
        )