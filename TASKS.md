# Task Plan for: Add Bank-Related Mock Emails from RBS and FI Bank

## Subtasks
1. [x] **Create bank email templates and data**
   - Complexity: Easy
   - Depends on: —
   - Description: Define realistic bank email templates for credit card overdraft, terms modifications, and other banking communications from RBS and FI Bank
   - Result: Created comprehensive bank email templates with 5 categories (overdraft, terms, security, statements, promotional) for both RBS and FI Bank, including realistic content in English and Bulgarian

2. [x] **Implement bank email generation function**
   - Complexity: Easy
   - Depends on: 1
   - Description: Create function to generate bank-specific emails with appropriate senders, subjects, and content
   - Result: Created generate_bank_email() function with realistic data generation and generate_bank_emails() MCP tool for creating multiple bank emails

3. [x] **Add bank emails to sample data**
   - Complexity: Easy
   - Depends on: 2
   - Description: Update the email server to include bank emails in initial generation and sample email creation
   - Result: Updated generate_initial_emails() to include 8 bank emails alongside 5 regular emails, providing a realistic mix of banking communications

4. [x] **Test bank email functionality**
   - Complexity: Easy
   - Depends on: 3
   - Description: Verify bank emails are generated correctly and can be searched/filtered appropriately
   - Result: Created comprehensive test suite that verified all 10 email types (5 per bank) generate correctly with proper priorities, tags, and searchable content

5. [x] **Fix email ID persistence issue**
   - Complexity: Easy
   - Depends on: 4
   - Description: Prevent email IDs from regenerating on every MCP server restart
   - Result: Modified email generation to only occur when inbox is empty, added initialize_email_inbox and get_inbox_status tools for controlled email management

6. [x] **Replace random generation with hardcoded emails**
   - Complexity: Easy
   - Depends on: 5
   - Description: Replace random email generation with fixed hardcoded emails for consistent testing
   - Result: Created 11 hardcoded emails with fixed IDs (3 regular + 8 bank emails from RBS and FI Bank) that initialize automatically on server startup 