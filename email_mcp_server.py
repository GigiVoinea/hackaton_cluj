"""
MCP Email Server - Simulates an email inbox with full email management capabilities.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from email_models import Email, EmailPriority, EmailStatus, email_inbox
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    log_level: str = Field(default="info")

# Sample email data for simulation
SAMPLE_SENDERS = [
    "john.doe@company.com",
    "sarah.wilson@bank.com", 
    "notifications@amazon.com",
    "team@slack.com",
    "billing@netflix.com",
    "support@github.com",
    "newsletter@techcrunch.com",
    "alerts@creditcard.com",
    "hr@company.com",
    "boss@company.com"
]

SAMPLE_SUBJECTS = [
    "Quarterly Financial Report",
    "Your Amazon order has shipped",
    "Weekly team standup notes",
    "Credit card statement available",
    "New GitHub notifications",
    "Your Netflix payment failed",
    "Tech industry news digest",
    "Urgent: Security alert",
    "Meeting reminder: 1:1 with manager",
    "Expense report approval needed"
]

SAMPLE_BODIES = [
    "Please review the attached quarterly financial report. The numbers look good this quarter with 15% growth.",
    "Your order #12345 has been shipped and will arrive by tomorrow. Track your package using the link below.",
    "Here are the notes from our weekly standup. Please review action items and update your status.",
    "Your credit card statement for December is now available. You have a balance of $1,247.83.",
    "You have 3 new notifications on GitHub. Check your repositories for recent activity.",
    "We were unable to process your Netflix payment. Please update your payment method to continue service.",
    "This week in tech: AI breakthroughs, new startup funding, and industry analysis.",
    "We detected unusual activity on your account. Please verify your recent transactions immediately.",
    "Don't forget about our 1:1 meeting scheduled for tomorrow at 2 PM. Come prepared with your updates.",
    "Your expense report from last month is pending approval. Please review and submit any missing receipts."
]

# Bank-specific email templates
BANK_SENDERS = {
    "RBS": [
        "noreply@rbs.co.uk",
        "creditcards@rbs.co.uk", 
        "customerservice@rbs.co.uk",
        "alerts@rbs.co.uk",
        "statements@rbs.co.uk",
        "security@rbs.co.uk",
        "overdrafts@rbs.co.uk"
    ],
    "FI_BANK": [
        "noreply@fibank.bg",
        "creditcards@fibank.bg",
        "customercare@fibank.bg", 
        "alerts@fibank.bg",
        "statements@fibank.bg",
        "security@fibank.bg",
        "overdrafts@fibank.bg"
    ]
}

BANK_EMAIL_TEMPLATES = {
    "credit_card_overdraft": {
        "subjects": [
            "URGENT: Credit Card Overdraft Notice - Account {account_number}",
            "Credit Card Limit Exceeded - Immediate Action Required",
            "Overdraft Alert: Your Credit Card Account {account_number}",
            "Important: Credit Card Overdraft Fees Applied"
        ],
        "bodies": {
            "RBS": [
                """Dear Valued Customer,

We are writing to inform you that your RBS Credit Card account {account_number} has exceeded its credit limit.

Current Balance: £{balance}
Credit Limit: £{credit_limit}
Overlimit Amount: £{overlimit_amount}
Overlimit Fee: £{fee}

To avoid additional charges, please make a payment immediately. You can:
- Pay online at rbs.co.uk
- Call our 24/7 helpline: 0345 724 2424
- Visit any RBS branch

Please note that interest will continue to accrue on the outstanding balance until paid in full.

If you have any questions, please contact our Customer Service team.

Kind regards,
RBS Credit Card Services

This is an automated message. Please do not reply to this email.""",
                """Dear Customer,

Your RBS Credit Card ending in {last_four} has gone over its credit limit.

Account Details:
- Account Number: {account_number}
- Current Balance: £{balance}
- Available Credit: £0.00
- Overlimit Fee Charged: £{fee}

Immediate payment is required to bring your account back within the credit limit. Failure to do so may result in:
- Additional overlimit fees
- Increased interest rates
- Suspension of card privileges

Make a payment now:
- Online Banking: rbs.co.uk
- Mobile App: RBS Mobile
- Phone: 0345 724 2424

Thank you for your immediate attention to this matter.

RBS Customer Services"""
            ],
            "FI_BANK": [
                """Уважаеми клиент,

Информираме Ви, че кредитната Ви карта с номер {account_number} е надвишила разрешения кредитен лимит.

Текущо салдо: {balance} лв.
Кредитен лимит: {credit_limit} лв.
Надвишение: {overlimit_amount} лв.
Такса за надвишение: {fee} лв.

За да избегнете допълнителни такси, моля извършете плащане незабавно:
- Онлайн банкиране: fibank.bg
- Мобилно приложение: Fibank Mobile
- Телефон: 0700 11 011

Лихвите ще продължат да се начисляват върху неплатената сума.

С уважение,
Екип Кредитни карти
Първа инвестиционна банка""",
                """Dear Customer,

Your FI Bank Credit Card account {account_number} has exceeded the approved credit limit.

Current Balance: BGN {balance}
Credit Limit: BGN {credit_limit}
Overlimit Amount: BGN {overlimit_amount}
Overlimit Fee: BGN {fee}

To restore your account to good standing, please make an immediate payment:
- Online: fibank.bg
- Mobile App: Fibank Mobile  
- Phone: +359 2 800 2000

Interest charges will continue to accrue until the balance is paid.

Best regards,
FI Bank Credit Card Services"""
            ]
        }
    },
    "terms_conditions": {
        "subjects": [
            "Important Changes to Your {bank_name} Account Terms and Conditions",
            "Updated Terms and Conditions - Action Required",
            "Notice of Changes to Your Banking Agreement",
            "Your {bank_name} Account Terms - Important Updates"
        ],
        "bodies": {
            "RBS": [
                """Dear Customer,

We are writing to inform you of important changes to the terms and conditions of your RBS account(s), effective from {effective_date}.

Key Changes Include:
• Updated overdraft fees and charges
• Changes to international transaction fees
• Modified dispute resolution procedures
• Updated data protection policies

What You Need to Do:
If you are happy with these changes, you don't need to do anything. The new terms will automatically apply from {effective_date}.

If you don't agree with the changes, you have the right to close your account without charge before {effective_date}.

Full Details:
The complete updated terms and conditions are available:
- Online at rbs.co.uk/terms
- At any RBS branch
- By calling 0345 724 2424

We value your business and thank you for choosing RBS.

Yours sincerely,
RBS Customer Services

Royal Bank of Scotland plc. Registered in Scotland No. SC083026.""",
                """Important Notice - Terms and Conditions Update

Dear RBS Customer,

This letter contains important information about changes to your account terms and conditions.

Effective Date: {effective_date}

Summary of Changes:
1. Overdraft Interest Rates - Updated pricing structure
2. Card Transaction Fees - New fees for certain international transactions  
3. Account Maintenance - Changes to monthly account fees
4. Digital Services - Updated terms for online and mobile banking

Your Rights:
- You may close your account without penalty before {effective_date}
- Continue using your account to accept these changes
- Contact us with any questions or concerns

For full terms: rbs.co.uk/legal or visit any branch.

Customer Service: 0345 724 2424

RBS - Here for you"""
            ],
            "FI_BANK": [
                """Уважаеми клиент,

Уведомяваме Ви за важни промени в общите условия на Вашата банкова сметка в Първа инвестиционна банка, които влизат в сила от {effective_date}.

Основни промени:
• Актуализирани такси за овърдрафт
• Промени в таксите за международни транзакции
• Обновени условия за дебитни и кредитни карти
• Актуализирана политика за защита на данните

Какво трябва да направите:
Ако сте съгласни с промените, не е необходимо да предприемате действия. Новите условия ще влязат в сила автоматично от {effective_date}.

Ако не сте съгласни с промените, имате право да закриете сметката си без такса преди {effective_date}.

Пълните условия можете да намерите на fibank.bg или в клон на банката.

За въпроси: 0700 11 011

С уважение,
Първа инвестиционна банка""",
                """Dear Valued Customer,

We are writing to inform you of important updates to the terms and conditions governing your FI Bank account, effective {effective_date}.

Changes Include:
• Revised fee structure for account maintenance
• Updated international transfer charges  
• Modified credit card terms and conditions
• Enhanced security measures and procedures

Your Options:
- Accept changes: Continue using your account normally
- Decline changes: Close account before {effective_date} without penalty

Complete terms available at fibank.bg/terms or any FI Bank branch.

Questions? Contact us at +359 2 800 2000

Best regards,
First Investment Bank"""
            ]
        }
    },
    "security_alerts": {
        "subjects": [
            "Security Alert: Unusual Activity on Your {bank_name} Account",
            "URGENT: Verify Your Recent Transaction",
            "Account Security Notice - Action Required",
            "Suspicious Activity Detected on Account {account_number}"
        ],
        "bodies": {
            "RBS": [
                """SECURITY ALERT

Dear Customer,

We have detected unusual activity on your RBS account ending in {last_four}.

Transaction Details:
Date: {transaction_date}
Amount: £{amount}
Location: {location}
Merchant: {merchant}

If you recognize this transaction, no action is required.

If you DO NOT recognize this transaction:
1. Call us immediately: 0345 724 2424
2. Log into online banking to review your account
3. Consider temporarily blocking your card

Your security is our priority. We monitor accounts 24/7 to protect against fraud.

Never share your PIN, passwords, or security details with anyone.

RBS Fraud Prevention Team

This is an automated security alert.""",
                """Account Security Notice

Dear RBS Customer,

Our fraud monitoring systems have flagged potential unauthorized activity on your account {account_number}.

Flagged Transaction:
- Amount: £{amount}
- Date: {transaction_date}  
- Description: {description}
- Status: PENDING VERIFICATION

Immediate Action Required:
Please verify this transaction by:
- Calling 0345 724 2424
- Logging into RBS online banking
- Visiting your nearest branch

Your card may be temporarily restricted until verification is complete.

If this transaction is fraudulent, we will:
- Block your card immediately
- Investigate the transaction
- Issue a replacement card
- Refund unauthorized charges

Stay vigilant against fraud.

RBS Security Team"""
            ],
            "FI_BANK": [
                """СИГУРНОСТ НА СМЕТКАТА

Уважаеми клиент,

Засякохме необичайна активност на Вашата сметка в Първа инвестиционна банка.

Детайли за транзакцията:
Дата: {transaction_date}
Сума: {amount} лв.
Локация: {location}
Търговец: {merchant}

Ако разпознавате тази транзакция, не е необходимо да предприемате действия.

Ако НЕ разпознавате транзакцията:
1. Обадете се незабавно: 0700 11 011
2. Влезте в интернет банкирането
3. Помислете за временно блокиране на картата

Вашата сигурност е наш приоритет.

Екип за сигурност
Първа инвестиционна банка""",
                """Security Alert - FI Bank

Dear Customer,

Our security systems have detected suspicious activity on your FI Bank account {account_number}.

Transaction Under Review:
Amount: BGN {amount}
Date: {transaction_date}
Location: {location}
Status: BLOCKED PENDING VERIFICATION

Required Action:
Please contact us immediately to verify this transaction:
- Phone: +359 2 800 2000
- Visit any FI Bank branch
- Use FI Bank mobile app

Your card has been temporarily blocked for security.

If verified as fraud, we will:
- Investigate immediately
- Issue new card within 3 business days
- Reverse unauthorized charges

FI Bank Security Department"""
            ]
        }
    },
    "statements": {
        "subjects": [
            "Your {bank_name} Monthly Statement is Ready",
            "Account Statement Available - {statement_month} {statement_year}",
            "Monthly Statement for Account {account_number}",
            "{bank_name} Statement - Please Review"
        ],
        "bodies": {
            "RBS": [
                """Dear Customer,

Your RBS monthly statement for {statement_month} {statement_year} is now available.

Account Summary:
Account Number: {account_number}
Statement Period: {start_date} to {end_date}
Opening Balance: £{opening_balance}
Closing Balance: £{closing_balance}
Total Transactions: {transaction_count}

To view your statement:
- Log in to RBS online banking
- Use the RBS mobile app
- Visit rbs.co.uk/statements

Important Reminders:
- Review all transactions carefully
- Report any discrepancies within 60 days
- Keep statements for your records

If you have questions about your statement, please contact us at 0345 724 2424.

Thank you for banking with RBS.

RBS Customer Services""",
                """Monthly Statement Available

Dear RBS Customer,

Your account statement for {statement_month} {statement_year} is ready for review.

Key Information:
- Account: {account_number}
- Period: {start_date} - {end_date}
- Transactions: {transaction_count}
- Fees Charged: £{fees}
- Interest Earned: £{interest}

Access Your Statement:
1. RBS Online Banking: rbs.co.uk
2. RBS Mobile App
3. Call 0345 724 2424 for postal copy

Please review your statement promptly and contact us if you notice any unauthorized transactions.

Going paperless? Switch to e-statements at rbs.co.uk/paperless

RBS - Here for you"""
            ],
            "FI_BANK": [
                """Уважаеми клиент,

Месечната Ви банкова сметка за {statement_month} {statement_year} е готова за преглед.

Обобщение на сметката:
Номер на сметка: {account_number}
Период: {start_date} до {end_date}
Начално салдо: {opening_balance} лв.
Крайно салдо: {closing_balance} лв.
Общо транзакции: {transaction_count}

За да видите сметката:
- Влезте в интернет банкирането на fibank.bg
- Използвайте мобилното приложение Fibank
- Посетете клон на банката

Важно:
- Прегледайте внимателно всички транзакции
- Съобщете за неточности в рамките на 60 дни

За въпроси: 0700 11 011

С уважение,
Първа инвестиционна банка""",
                """Monthly Statement - FI Bank

Dear Customer,

Your FI Bank account statement for {statement_month} {statement_year} is now available.

Account Details:
- Account Number: {account_number}
- Statement Period: {start_date} to {end_date}
- Opening Balance: BGN {opening_balance}
- Closing Balance: BGN {closing_balance}
- Number of Transactions: {transaction_count}

View Your Statement:
- Online banking: fibank.bg
- Mobile app: Fibank Mobile
- Branch visit for printed copy

Please review all transactions and report any discrepancies within 60 days.

For assistance: +359 2 800 2000

Best regards,
First Investment Bank"""
            ]
        }
    },
    "promotional": {
        "subjects": [
            "Exclusive Offer: New {bank_name} Credit Card with 0% APR",
            "Limited Time: Increase Your Credit Limit",
            "Special Rates on {bank_name} Personal Loans",
            "Invitation: Premium Banking Benefits"
        ],
        "bodies": {
            "RBS": [
                """Dear Valued Customer,

We're pleased to offer you an exclusive opportunity to apply for the new RBS Rewards Credit Card.

Special Launch Offer:
• 0% APR for 18 months on purchases
• 0% APR for 12 months on balance transfers
• No annual fee for the first year
• Earn 2% cashback on all purchases

Why Choose RBS Rewards Card:
- Competitive rates after promotional period
- 24/7 customer support
- Comprehensive fraud protection
- Mobile app with spending insights

Pre-approved Amount: Up to £{credit_limit}

Apply now:
- Online at rbs.co.uk/creditcards
- Call 0345 724 2424
- Visit any RBS branch

This offer expires on {expiry_date}.

Terms and conditions apply. Representative APR 22.9% variable.

RBS Credit Card Team""",
                """Exclusive Banking Offer

Dear RBS Customer,

Based on your excellent account history, we're delighted to offer you preferential rates on our personal loan products.

Your Exclusive Rates:
- Personal Loan: From 3.9% APR
- Home Improvement Loan: From 4.2% APR  
- Car Finance: From 4.5% APR

Loan amounts from £1,000 to £50,000
Repayment terms: 1-7 years

Benefits:
✓ No arrangement fees
✓ Early repayment options
✓ Fixed monthly payments
✓ Quick online application

Get your quote in minutes at rbs.co.uk/loans

Offer valid until {expiry_date}

Representative example: £10,000 over 5 years at 3.9% APR = £184.07 per month.

RBS Lending Team"""
            ],
            "FI_BANK": [
                """Специално предложение за Вас

Уважаеми клиент,

Имаме удоволствието да Ви предложим ексклузивни условия за нова кредитна карта от Първа инвестиционна банка.

Специални условия:
• 0% лихва за първите 12 месеца
• Без годишна такса за първата година
• До 2% кешбек от покупките
• Безплатно теглене на кеш в банкомати на ПИБ

Предварително одобрена сума: до {credit_limit} лв.

Кандидатствайте:
- Онлайн на fibank.bg
- Телефон: 0700 11 011
- В клон на банката

Офертата е валидна до {expiry_date}.

Представителен ГПР: 24.9% променлив.

С уважение,
Екип Кредитни карти
Първа инвестиционна банка""",
                """Exclusive Personal Loan Offer

Dear FI Bank Customer,

We are pleased to offer you preferential interest rates on personal loans based on your excellent banking relationship.

Your Special Rates:
- Personal Loan: From 8.9% APR
- Home Renovation: From 9.2% APR
- Education Loan: From 7.5% APR

Loan Features:
• Amounts from BGN 1,000 to BGN 100,000
• Flexible repayment: 12-84 months
• No early repayment penalties
• Quick approval process

Apply today:
- Online: fibank.bg/loans
- Phone: +359 2 800 2000
- Visit any branch

Offer expires: {expiry_date}

Representative example: BGN 20,000 over 5 years at 8.9% APR = BGN 415.32 monthly.

FI Bank Personal Banking"""
            ]
        }
    }
}

# Initialize settings and MCP server
settings = Settings()
mcp = FastMCP("Email Inbox", settings=settings.model_dump())

@mcp.tool()
async def list_emails(folder: str = "inbox", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """List emails in a specific folder (inbox, sent, drafts, trash, spam, archive)."""
    try:
        emails = email_inbox.list_emails(folder, limit, offset)
        
        if not emails:
            return {
                "success": True,
                "emails": [],
                "message": f"No emails found in {folder} folder.",
                "folder": folder,
                "count": 0
            }
        
        email_list = []
        for email in emails:
            status_icon = "📧" if email.status == EmailStatus.UNREAD else "📖"
            priority_icon = "🔴" if email.priority in [EmailPriority.HIGH, EmailPriority.URGENT] else ""
            
            email_list.append({
                "id": email.email_id,
                "subject": email.subject,
                "sender": email.sender,
                "date": email.timestamp.strftime('%Y-%m-%d %H:%M'),
                "status": email.status.value,
                "priority": email.priority.value,
                "display": f"{status_icon} {priority_icon} **{email.subject}**\n   From: {email.sender}\n   Date: {email.timestamp.strftime('%Y-%m-%d %H:%M')}\n   ID: {email.email_id}\n   Status: {email.status.value}\n"
            })
        
        return {
            "success": True,
            "emails": email_list,
            "folder": folder,
            "count": len(emails),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        return {
            "success": False,
            "emails": [],
            "error": str(e),
            "folder": folder
        }

@mcp.tool()
async def read_email(email_id: str) -> Dict[str, Any]:
    """Read the full content of a specific email by ID."""
    try:
        email = email_inbox.get_email(email_id)
        
        if not email:
            return {
                "success": False,
                "email": None,
                "error": f"Email with ID {email_id} not found."
            }
        
        # Mark as read when viewing
        email_inbox.mark_as_read(email_id)
        
        return {
            "success": True,
            "email": {
                "id": email.email_id,
                "subject": email.subject,
                "sender": email.sender,
                "recipients": email.recipients,
                "cc": email.cc,
                "bcc": email.bcc,
                "body": email.body,
                "html_body": email.html_body,
                "timestamp": email.timestamp.isoformat(),
                "status": email.status.value,
                "priority": email.priority.value,
                "folder": email.folder,
                "attachments": [
                    {
                        "filename": att.filename,
                        "size": att.size,
                        "content_type": att.content_type,
                        "id": att.attachment_id
                    } for att in email.attachments
                ],
                "tags": email.tags
            }
        }
    except Exception as e:
        return {
            "success": False,
            "email": None,
            "error": str(e)
        }

@mcp.tool()
async def search_emails(query: str, folder: str = None) -> Dict[str, Any]:
    """Search emails by subject, sender, or content."""
    try:
        results = email_inbox.search_emails(query, folder)
        
        if not results:
            search_scope = f" in {folder}" if folder else ""
            return {
                "success": True,
                "emails": [],
                "message": f"No emails found matching '{query}'{search_scope}.",
                "query": query,
                "folder": folder,
                "count": 0
            }
        
        email_list = []
        for email in results:
            status_icon = "📧" if email.status == EmailStatus.UNREAD else "📖"
            email_list.append({
                "id": email.email_id,
                "subject": email.subject,
                "sender": email.sender,
                "date": email.timestamp.strftime('%Y-%m-%d %H:%M'),
                "folder": email.folder,
                "status": email.status.value,
                "priority": email.priority.value,
                "display": f"{status_icon} **{email.subject}**\n   From: {email.sender}\n   Date: {email.timestamp.strftime('%Y-%m-%d %H:%M')}\n   Folder: {email.folder}\n   ID: {email.email_id}\n"
            })
        
        return {
            "success": True,
            "emails": email_list,
            "query": query,
            "folder": folder,
            "count": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "emails": [],
            "error": str(e),
            "query": query,
            "folder": folder
        }

@mcp.tool()
async def mark_email_read(email_id: str) -> Dict[str, Any]:
    """Mark an email as read."""
    try:
        success = email_inbox.mark_as_read(email_id)
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_id} marked as read.",
                "email_id": email_id
            }
        else:
            return {
                "success": False,
                "message": f"Could not mark email {email_id} as read. Email not found or already read.",
                "email_id": email_id
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "email_id": email_id
        }

@mcp.tool()
async def delete_email(email_id: str) -> Dict[str, Any]:
    """Delete an email (move to trash or permanent delete if already in trash)."""
    try:
        success = email_inbox.delete_email(email_id)
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_id} deleted successfully.",
                "email_id": email_id
            }
        else:
            return {
                "success": False,
                "message": f"Could not delete email {email_id}. Email not found.",
                "email_id": email_id
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "email_id": email_id
        }

@mcp.tool()
async def move_email(email_id: str, target_folder: str) -> Dict[str, Any]:
    """Move an email to a different folder."""
    try:
        success = email_inbox.move_email(email_id, target_folder)
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_id} moved to {target_folder} folder.",
                "email_id": email_id,
                "target_folder": target_folder
            }
        else:
            return {
                "success": False,
                "message": f"Could not move email {email_id} to {target_folder}. Email or folder not found.",
                "email_id": email_id,
                "target_folder": target_folder
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "email_id": email_id,
            "target_folder": target_folder
        }

@mcp.tool()
async def send_email(to: List[str], subject: str, body: str, cc: List[str] = None, priority: str = "normal") -> Dict[str, Any]:
    """Send a new email."""
    try:
        if cc is None:
            cc = []
        
        priority_enum = EmailPriority(priority)
        
        # Create new email in sent folder
        new_email = Email(
            subject=subject,
            sender="user@example.com",  # Simulated user email
            recipients=to,
            cc=cc,
            body=body,
            priority=priority_enum,
            folder="sent",
            status=EmailStatus.READ  # Sent emails are marked as read
        )
        
        email_id = email_inbox.add_email(new_email)
        
        return {
            "success": True,
            "message": "Email sent successfully!",
            "email_id": email_id,
            "to": to,
            "subject": subject,
            "cc": cc,
            "priority": priority
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "to": to,
            "subject": subject
        }

@mcp.tool()
async def get_inbox_status() -> Dict[str, Any]:
    """Get current inbox status including email counts and initialization state."""
    try:
        total_emails = len(email_inbox.emails)
        
        if total_emails == 0:
            return {
                "success": True,
                "status": "empty",
                "total_emails": 0,
                "bank_emails": 0,
                "regular_emails": 0,
                "message": "Email inbox is empty. Use initialize_email_inbox to populate with sample emails.",
                "initialized": False
            }
        
        # Count bank emails
        bank_emails = [email for email in email_inbox.emails.values() 
                      if any(tag in ['rbs', 'fi_bank'] for tag in email.tags)]
        
        # Count unread emails
        unread_emails = [email for email in email_inbox.emails.values() 
                        if email.status == EmailStatus.UNREAD]
        
        return {
            "success": True,
            "status": "initialized",
            "total_emails": total_emails,
            "bank_emails": len(bank_emails),
            "regular_emails": total_emails - len(bank_emails),
            "unread_emails": len(unread_emails),
            "message": f"Email inbox contains {total_emails} emails ({len(bank_emails)} bank emails, {len(unread_emails)} unread)",
            "initialized": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

@mcp.tool()
async def get_folder_summary() -> Dict[str, Any]:
    """Get summary of all email folders with counts."""
    try:
        summary = []
        for folder_name, folder in email_inbox.folders.items():
            unread_text = f" ({folder.unread_count} unread)" if folder.unread_count > 0 else ""
            summary.append({
                "name": folder_name,
                "display_name": folder_name.title(),
                "email_count": folder.email_count,
                "unread_count": folder.unread_count,
                "display": f"📁 **{folder_name.title()}**: {folder.email_count} emails{unread_text}"
            })
        
        return {
            "success": True,
            "folders": summary,
            "total_folders": len(summary)
        }
    except Exception as e:
        return {
            "success": False,
            "folders": [],
            "error": str(e)
        }

def generate_bank_email(email_type: str, bank: str) -> Email:
    """Generate a realistic bank email with proper formatting and data."""
    template = BANK_EMAIL_TEMPLATES[email_type]
    
    # Generate realistic account data
    account_number = f"****{random.randint(1000, 9999)}"
    last_four = str(random.randint(1000, 9999))
    
    # Generate realistic financial amounts
    if email_type == "credit_card_overdraft":
        credit_limit = random.randint(1000, 10000)
        balance = credit_limit + random.randint(50, 500)
        overlimit_amount = balance - credit_limit
        fee = random.choice([25, 35, 50])
        
        format_data = {
            "account_number": account_number,
            "last_four": last_four,
            "balance": f"{balance:,.2f}",
            "credit_limit": f"{credit_limit:,.2f}",
            "overlimit_amount": f"{overlimit_amount:,.2f}",
            "fee": f"{fee:.2f}",
            "bank_name": "RBS" if bank == "RBS" else "FI Bank"
        }
    elif email_type == "terms_conditions":
        effective_date = (datetime.now() + timedelta(days=random.randint(30, 60))).strftime("%d %B %Y")
        format_data = {
            "bank_name": "RBS" if bank == "RBS" else "FI Bank",
            "effective_date": effective_date
        }
    elif email_type == "security_alerts":
        amount = random.randint(50, 2000)
        transaction_date = (datetime.now() - timedelta(days=random.randint(0, 3))).strftime("%d/%m/%Y")
        locations = ["London, UK", "Manchester, UK", "Edinburgh, UK", "Sofia, Bulgaria", "Plovdiv, Bulgaria", "Varna, Bulgaria"]
        merchants = ["Amazon UK", "Tesco", "Sainsbury's", "Shell", "McDonald's", "Zara", "H&M", "Kaufland", "Billa"]
        
        format_data = {
            "account_number": account_number,
            "last_four": last_four,
            "amount": f"{amount:.2f}",
            "transaction_date": transaction_date,
            "location": random.choice(locations),
            "merchant": random.choice(merchants),
            "description": f"Card payment at {random.choice(merchants)}",
            "bank_name": "RBS" if bank == "RBS" else "FI Bank"
        }
    elif email_type == "statements":
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        statement_month = random.choice(months)
        statement_year = "2024"
        start_date = f"01 {statement_month} {statement_year}"
        end_date = f"{random.randint(28, 31)} {statement_month} {statement_year}"
        
        opening_balance = random.randint(500, 5000)
        closing_balance = opening_balance + random.randint(-200, 300)
        transaction_count = random.randint(15, 45)
        fees = random.randint(0, 25)
        interest = random.randint(0, 15)
        
        format_data = {
            "bank_name": "RBS" if bank == "RBS" else "FI Bank",
            "account_number": account_number,
            "statement_month": statement_month,
            "statement_year": statement_year,
            "start_date": start_date,
            "end_date": end_date,
            "opening_balance": f"{opening_balance:,.2f}",
            "closing_balance": f"{closing_balance:,.2f}",
            "transaction_count": transaction_count,
            "fees": f"{fees:.2f}",
            "interest": f"{interest:.2f}"
        }
    elif email_type == "promotional":
        credit_limit = random.randint(2000, 15000)
        expiry_date = (datetime.now() + timedelta(days=random.randint(14, 45))).strftime("%d %B %Y")
        
        format_data = {
            "bank_name": "RBS" if bank == "RBS" else "FI Bank",
            "credit_limit": f"{credit_limit:,}",
            "expiry_date": expiry_date
        }
    else:
        format_data = {}
    
    # Select random subject and body
    subject = random.choice(template["subjects"]).format(**format_data)
    body = random.choice(template["bodies"][bank]).format(**format_data)
    
    # Select appropriate sender
    sender = random.choice(BANK_SENDERS[bank])
    
    # Set priority based on email type
    if email_type in ["credit_card_overdraft", "security_alerts"]:
        priority = random.choice([EmailPriority.HIGH, EmailPriority.URGENT])
    elif email_type == "terms_conditions":
        priority = EmailPriority.HIGH
    else:
        priority = EmailPriority.NORMAL
    
    # Random timestamp within last 14 days
    days_ago = random.randint(0, 14)
    hours_ago = random.randint(0, 23)
    timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
    
    return Email(
        subject=subject,
        sender=sender,
        recipients=["user@example.com"],
        body=body,
        timestamp=timestamp,
        priority=priority,
        tags=["banking", bank.lower(), email_type]
    )

@mcp.tool()
async def generate_bank_emails(count: int = 10) -> Dict[str, Any]:
    """Generate realistic bank emails from RBS and FI Bank covering various banking scenarios."""
    try:
        generated_emails = []
        email_types = list(BANK_EMAIL_TEMPLATES.keys())
        banks = ["RBS", "FI_BANK"]
        
        for i in range(count):
            # Randomly select bank and email type
            bank = random.choice(banks)
            email_type = random.choice(email_types)
            
            # Generate the email
            email = generate_bank_email(email_type, bank)
            email_id = email_inbox.add_email(email)
            
            generated_emails.append({
                "id": email_id,
                "subject": email.subject,
                "sender": email.sender,
                "type": email_type,
                "bank": bank,
                "priority": email.priority.value,
                "display": f"🏦 {email.subject} (from {email.sender})"
            })
        
        return {
            "success": True,
            "generated_emails": generated_emails,
            "count": count,
            "message": f"Generated {count} bank emails from RBS and FI Bank"
        }
    except Exception as e:
        return {
            "success": False,
            "generated_emails": [],
            "error": str(e),
            "count": count
        }

@mcp.tool()
async def initialize_email_inbox() -> Dict[str, Any]:
    """Initialize the email inbox with sample emails if it's empty."""
    try:
        if len(email_inbox.emails) > 0:
            return {
                "success": True,
                "message": f"Email inbox already initialized with {len(email_inbox.emails)} emails",
                "email_count": len(email_inbox.emails),
                "action": "skipped"
            }
        
        # Initialize hardcoded emails
        initialize_hardcoded_emails()
        
        # Count bank emails
        bank_emails = [email for email in email_inbox.emails.values() 
                      if any(tag in ['rbs', 'fi_bank'] for tag in email.tags)]
        
        return {
            "success": True,
            "message": f"Email inbox initialized successfully",
            "total_emails": len(email_inbox.emails),
            "bank_emails": len(bank_emails),
            "regular_emails": len(email_inbox.emails) - len(bank_emails),
            "action": "initialized"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action": "failed"
        }

@mcp.tool()
async def generate_sample_emails(count: int = 5) -> Dict[str, Any]:
    """Generate sample emails for testing (simulates receiving new emails)."""
    try:
        generated_emails = []
        for i in range(count):
            # Generate random email
            sender = random.choice(SAMPLE_SENDERS)
            subject = random.choice(SAMPLE_SUBJECTS)
            body = random.choice(SAMPLE_BODIES)
            
            # Random timestamp within last 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            # Random priority (mostly normal)
            priority = random.choices(
                [EmailPriority.LOW, EmailPriority.NORMAL, EmailPriority.HIGH, EmailPriority.URGENT],
                weights=[10, 70, 15, 5]
            )[0]
            
            email = Email(
                subject=subject,
                sender=sender,
                recipients=["user@example.com"],
                body=body,
                timestamp=timestamp,
                priority=priority
            )
            
            email_id = email_inbox.add_email(email)
            generated_emails.append({
                "id": email_id,
                "subject": subject,
                "sender": sender,
                "display": f"📧 {subject} (from {sender})"
            })
        
        return {
            "success": True,
            "generated_emails": generated_emails,
            "count": count,
            "message": f"Generated {count} sample emails"
        }
    except Exception as e:
        return {
            "success": False,
            "generated_emails": [],
            "error": str(e),
            "count": count
        }

def initialize_hardcoded_emails():
    """Initialize inbox with hardcoded emails that have fixed IDs."""
    # Only initialize if inbox is empty
    if len(email_inbox.emails) > 0:
        logger.info(f"Email inbox already has {len(email_inbox.emails)} emails, skipping initialization")
        return
        
    logger.info("Initializing hardcoded emails...")
    
    # Hardcoded emails with fixed IDs and content
    hardcoded_emails = [
        # Regular emails
        Email(
            email_id="email-001-regular",
            subject="Quarterly Financial Report",
            sender="john.doe@company.com",
            recipients=["user@example.com"],
            body="Please review the attached quarterly financial report. The numbers look good this quarter with 15% growth. We've seen significant improvements in our revenue streams and cost management.",
            timestamp=datetime.now() - timedelta(days=2, hours=3),
            priority=EmailPriority.NORMAL
        ),
        Email(
            email_id="email-002-regular",
            subject="Meeting reminder: 1:1 with manager",
            sender="boss@company.com",
            recipients=["user@example.com"],
            body="Don't forget about our 1:1 meeting scheduled for tomorrow at 2 PM. Come prepared with your updates on the current projects and any blockers you're facing.",
            timestamp=datetime.now() - timedelta(days=1, hours=5),
            priority=EmailPriority.HIGH
        ),
        Email(
            email_id="email-003-regular",
            subject="Your Amazon order has shipped",
            sender="notifications@amazon.com",
            recipients=["user@example.com"],
            body="Your order #AMZ-12345 has been shipped and will arrive by tomorrow. Track your package using the link below. Thank you for shopping with Amazon.",
            timestamp=datetime.now() - timedelta(days=3, hours=1),
            priority=EmailPriority.LOW
        ),
        
        # RBS Bank emails
        Email(
            email_id="rbs-001-overdraft",
            subject="URGENT: Credit Card Overdraft Notice - Account ****4527",
            sender="overdrafts@rbs.co.uk",
            recipients=["user@example.com"],
            body="""Dear Valued Customer,

We are writing to inform you that your RBS Credit Card account ****4527 has exceeded its credit limit.

Current Balance: £2,750.00
Credit Limit: £2,500.00
Overlimit Amount: £250.00
Overlimit Fee: £35.00

To avoid additional charges, please make a payment immediately. You can:
- Pay online at rbs.co.uk
- Call our 24/7 helpline: 0345 724 2424
- Visit any RBS branch

Please note that interest will continue to accrue on the outstanding balance until paid in full.

If you have any questions, please contact our Customer Service team.

Kind regards,
RBS Credit Card Services

This is an automated message. Please do not reply to this email.""",
            timestamp=datetime.now() - timedelta(hours=6),
            priority=EmailPriority.URGENT,
            tags=["banking", "rbs", "credit_card_overdraft"]
        ),
        Email(
            email_id="rbs-002-security",
            subject="URGENT: Verify Your Recent Transaction",
            sender="security@rbs.co.uk",
            recipients=["user@example.com"],
            body="""SECURITY ALERT

Dear Customer,

We have detected unusual activity on your RBS account ending in 4527.

Transaction Details:
Date: 25/01/2025
Amount: £450.00
Location: London, UK
Merchant: Amazon UK

If you recognize this transaction, no action is required.

If you DO NOT recognize this transaction:
1. Call us immediately: 0345 724 2424
2. Log into online banking to review your account
3. Consider temporarily blocking your card

Your security is our priority. We monitor accounts 24/7 to protect against fraud.

Never share your PIN, passwords, or security details with anyone.

RBS Fraud Prevention Team

This is an automated security alert.""",
            timestamp=datetime.now() - timedelta(days=1, hours=2),
            priority=EmailPriority.URGENT,
            tags=["banking", "rbs", "security_alerts"]
        ),
        Email(
            email_id="rbs-003-statement",
            subject="Your RBS Monthly Statement is Ready",
            sender="statements@rbs.co.uk",
            recipients=["user@example.com"],
            body="""Dear Customer,

Your RBS monthly statement for January 2025 is now available.

Account Summary:
Account Number: ****4527
Statement Period: 01 January 2025 to 31 January 2025
Opening Balance: £1,250.00
Closing Balance: £2,750.00
Total Transactions: 28

To view your statement:
- Log in to RBS online banking
- Use the RBS mobile app
- Visit rbs.co.uk/statements

Important Reminders:
- Review all transactions carefully
- Report any discrepancies within 60 days
- Keep statements for your records

If you have questions about your statement, please contact us at 0345 724 2424.

Thank you for banking with RBS.

RBS Customer Services""",
            timestamp=datetime.now() - timedelta(days=3, hours=8),
            priority=EmailPriority.NORMAL,
            tags=["banking", "rbs", "statements"]
        ),
        Email(
            email_id="rbs-004-terms",
            subject="Important Changes to Your RBS Account Terms and Conditions",
            sender="customerservice@rbs.co.uk",
            recipients=["user@example.com"],
            body="""Dear Customer,

We are writing to inform you of important changes to the terms and conditions of your RBS account(s), effective from 15 March 2025.

Key Changes Include:
• Updated overdraft fees and charges
• Changes to international transaction fees
• Modified dispute resolution procedures
• Updated data protection policies

What You Need to Do:
If you are happy with these changes, you don't need to do anything. The new terms will automatically apply from 15 March 2025.

If you don't agree with the changes, you have the right to close your account without charge before 15 March 2025.

Full Details:
The complete updated terms and conditions are available:
- Online at rbs.co.uk/terms
- At any RBS branch
- By calling 0345 724 2424

We value your business and thank you for choosing RBS.

Yours sincerely,
RBS Customer Services

Royal Bank of Scotland plc. Registered in Scotland No. SC083026.""",
            timestamp=datetime.now() - timedelta(days=5, hours=4),
            priority=EmailPriority.HIGH,
            tags=["banking", "rbs", "terms_conditions"]
        ),
        
        # FI Bank emails
        Email(
            email_id="fibank-001-overdraft",
            subject="URGENT: Credit Card Overdraft Notice - Account ****8194",
            sender="overdrafts@fibank.bg",
            recipients=["user@example.com"],
            body="""Уважаеми клиент,

Информираме Ви, че кредитната Ви карта с номер ****8194 е надвишила разрешения кредитен лимит.

Текущо салдо: 3,250.00 лв.
Кредитен лимит: 3,000.00 лв.
Надвишение: 250.00 лв.
Такса за надвишение: 50.00 лв.

За да избегнете допълнителни такси, моля извършете плащане незабавно:
- Онлайн банкиране: fibank.bg
- Мобилно приложение: Fibank Mobile
- Телефон: 0700 11 011

Лихвите ще продължат да се начисляват върху неплатената сума.

С уважение,
Екип Кредитни карти
Първа инвестиционна банка""",
            timestamp=datetime.now() - timedelta(hours=12),
            priority=EmailPriority.URGENT,
            tags=["banking", "fi_bank", "credit_card_overdraft"]
        ),
        Email(
            email_id="fibank-002-security",
            subject="Security Alert: Unusual Activity on Your FI Bank Account",
            sender="security@fibank.bg",
            recipients=["user@example.com"],
            body="""СИГУРНОСТ НА СМЕТКАТА

Уважаеми клиент,

Засякохме необичайна активност на Вашата сметка в Първа инвестиционна банка.

Детайли за транзакцията:
Дата: 24/01/2025
Сума: 320.00 лв.
Локация: Sofia, Bulgaria
Търговец: Kaufland

Ако разпознавате тази транзакция, не е необходимо да предприемате действия.

Ако НЕ разпознавате транзакцията:
1. Обадете се незабавно: 0700 11 011
2. Влезте в интернет банкирането
3. Помислете за временно блокиране на картата

Вашата сигурност е наш приоритет.

Екип за сигурност
Първа инвестиционна банка""",
            timestamp=datetime.now() - timedelta(days=1, hours=8),
            priority=EmailPriority.HIGH,
            tags=["banking", "fi_bank", "security_alerts"]
        ),
        Email(
            email_id="fibank-003-statement",
            subject="Account Statement Available - January 2025",
            sender="statements@fibank.bg",
            recipients=["user@example.com"],
            body="""Уважаеми клиент,

Месечната Ви банкова сметка за January 2025 е готова за преглед.

Обобщение на сметката:
Номер на сметка: ****8194
Период: 01 January 2025 до 31 January 2025
Начално салдо: 2,500.00 лв.
Крайно салдо: 3,250.00 лв.
Общо транзакции: 22

За да видите сметката:
- Влезте в интернет банкирането на fibank.bg
- Използвайте мобилното приложение Fibank
- Посетете клон на банката

Важно:
- Прегледайте внимателно всички транзакции
- Съобщете за неточности в рамките на 60 дни

За въпроси: 0700 11 011

С уважение,
Първа инвестиционна банка""",
            timestamp=datetime.now() - timedelta(days=4, hours=6),
            priority=EmailPriority.NORMAL,
            tags=["banking", "fi_bank", "statements"]
        ),
        Email(
            email_id="fibank-004-promotional",
            subject="Exclusive Offer: New FI Bank Credit Card with 0% APR",
            sender="creditcards@fibank.bg",
            recipients=["user@example.com"],
            body="""Специално предложение за Вас

Уважаеми клиент,

Имаме удоволствието да Ви предложим ексклузивни условия за нова кредитна карта от Първа инвестиционна банка.

Специални условия:
• 0% лихва за първите 12 месеца
• Без годишна такса за първата година
• До 2% кешбек от покупките
• Безплатно теглене на кеш в банкомати на ПИБ

Предварително одобрена сума: до 5,000 лв.

Кандидатствайте:
- Онлайн на fibank.bg
- Телефон: 0700 11 011
- В клон на банката

Офертата е валидна до 28 February 2025.

Представителен ГПР: 24.9% променлив.

С уважение,
Екип Кредитни карти
Първа инвестиционна банка""",
            timestamp=datetime.now() - timedelta(days=6, hours=2),
            priority=EmailPriority.NORMAL,
            tags=["banking", "fi_bank", "promotional"]
        )
    ]
    
    # Add all hardcoded emails to inbox
    for email in hardcoded_emails:
        email_inbox.emails[email.email_id] = email
        # Update folder counts
        email_inbox._update_folder_counts(email.folder)
    
    logger.info(f"Initialized {len(hardcoded_emails)} hardcoded emails (3 regular + 8 bank emails)")

if __name__ == "__main__":
    # Initialize hardcoded emails on startup
    initialize_hardcoded_emails()
    
    # Run the MCP server using stdio transport
    mcp.run(transport="stdio") 