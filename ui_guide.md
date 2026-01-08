# G-Wallet | UI Interaction Guide

This guide explains how to use the G-Wallet Control Panel to manage wallets and demonstrate the system's hardened transactional correctness.

---

## 🧭 Navigation Flow
The UI uses an explicit Single Page Application (SPA) flow:
**Login** ➔ **Dashboard** ➔ **Actions (Create/Deposit/Transfer/History/Profile)** ➔ **Dashboard**

---

## 🖼️ Page Breakdown

### 1. Login Page
The entry point for the authenticated session.
- **Username**: Your unique handle (provisioned during the Build Phase or via API).
- **Authenticate Button**: Exchanges the username for a JWT (JSON Web Token).
- **Correctness Logic**: Demonstrates **JWT-based Authentication**. No sensitive user data is stored in the browser except the encrypted token.

### 2. Main Dashboard
Your primary navigation hub and asset overview.
- **Wallet Cards**: Summarizes your active funds. 
    - **Wallet #ID**: The primary key from the database.
    - **Balance**: Current atomic balance.
- **Action Buttons**: Quick links to money movement pages.

### 3. Create Wallet Page
Provisioning new cryptographic assets.
- **Confirm Provisioning**: Submits a body-less request.
- **Correctness Logic**: Demonstrates **Zero user_id Leakage**. The backend identifies your account via the JWT, ensuring users cannot create wallets for others by spoofing IDs in the request body.

### 4. Add Money (Deposit)
Funding your account.
- **Select Wallet**: A dropdown list of wallets *you* own.
- **Amount (USD)**: The value to add.
- **Correctness Logic**: Demonstrates **Invariant Enforcement**. The backend rejects negative amounts, preventing malicious "withdrawals" via the deposit endpoint.

### 5. Secure Transfer Page (The Core Demo)
Orchestrating atomic movement between accounts.
- **From Wallet**: Select which of your wallets will be debited.
- **To Wallet ID**: Manual input of any target Wallet ID in the system.
- **Amount (USD)**: Value to transfer.
- **Idempotency Key**: A unique, auto-generated tracker (e.g., `tx_abc123`). 
- **Correctness Logic**:
    - **Pessimistic Locking**: Concurrent transfers on the same wallet are serialized.
    - **Idempotency**: If you submit the same form twice, the auto-generated key ensures money is only moved once.
    - **Atomicity**: The system ensures either both the debit and credit succeed, or neither do.

### 6. Audit History Page
Immutable verification of all movements.
- **Select Wallet**: View the trail for a specific asset.
- **History Table**: Shows Time, Direction (From/To), Amount, and status.
- **Correctness Logic**: Demonstrates **Immutable Audit Logging**. Post-transaction records are stored permanently for verification.

### 7. User Profile Page
Read-only overview of your identity.
- **Identity Card**: Shows username and email extracted from the secure session.
- **Asset Overview**: Lists all wallets and their current state.

---

## 🛠 Troubleshooting
- **Unauthorized**: If your session expires, the UI will automatically redirect you to the Login page.
- **Transfer Failure**: If a transfer fails (e.g., insufficient funds), a clear red error message will appear explaining the rejection from the backend.
