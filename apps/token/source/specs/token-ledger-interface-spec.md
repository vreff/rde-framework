# Token Ledger Interface Specification

Source models:
- `models/feature-model/manual/prelude.cfr`
- `models/feature-model/manual/architecture.cfr`
- `models/feature-model/generated/requirements.generated.cfr`

## Service Boundary

Service: `TokenLedgerService`

Responsibilities:
- Apply deposit updates
- Apply transfer updates
- Settle or reject pending withdrawals
- Enforce preconditions and invariants corresponding to Clafer transition components

## Requirement IDs

- `nooverdraft`
- `balanceconsistency`
- `singlesource`
- `transfervalidity`
- `pendingsettlement`

## Operations

### deposit

Signature:
- Input: `DepositRequest(accountId, amount)`
- Output: `DepositResult(beforeBalance, afterBalance, totalSupplyAfter)`

Preconditions:
- amount > 0

Postconditions:
- afterBalance = beforeBalance + amount
- afterBalance >= 0

Traceability:
- preserves: `nooverdraft`, `balanceconsistency`
- scenarios: `successfulDepositScenario`

### transfer

Signature:
- Input: `TransferRequest(senderId, receiverId, amount)`
- Output: `TransferResult(senderBefore, senderAfter, receiverBefore, receiverAfter, totalSupplyAfter)`

Preconditions:
- sender and receiver are valid accounts
- amount > 0

Postconditions:
- senderAfter = senderBefore - amount
- receiverAfter = receiverBefore + amount
- senderAfter >= 0
- senderBefore + receiverBefore = senderAfter + receiverAfter
- totalSupply unchanged by transfer

Traceability:
- preserves: `singlesource`, `balanceconsistency`, `nooverdraft`, `transfervalidity`
- scenarios: `successfulTransferScenario`, `invalidTransferScenario`

### requestWithdrawal

Signature:
- Input: `WithdrawalRequest(accountId, amount)`
- Output: `PendingWithdrawal(id, accountId, amount, status)`

Preconditions:
- amount > 0

Postconditions:
- pending withdrawal record created

Traceability:
- preserves: `pendingsettlement`, `nooverdraft`
- scenarios: `insufficientBalanceScenario`, `pendingWithdrawalSettlementScenario`

### settleWithdrawal

Signature:
- Input: `SettleWithdrawalRequest(withdrawalId)`
- Output: `SettleWithdrawalResult(beforeBalance, afterBalance, status)`

Preconditions:
- pending withdrawal exists
- withdrawal amount <= beforeBalance

Postconditions:
- afterBalance = beforeBalance - withdrawalAmount
- afterBalance >= 0
- pending status becomes `settled`

Traceability:
- preserves: `pendingsettlement`, `balanceconsistency`, `nooverdraft`
- scenarios: `pendingWithdrawalSettlementScenario`

### rejectWithdrawal

Signature:
- Input: `RejectWithdrawalRequest(withdrawalId, reason)`
- Output: `RejectWithdrawalResult(beforeBalance, afterBalance, status)`

Preconditions:
- pending withdrawal exists

Postconditions:
- beforeBalance = afterBalance
- pending status becomes `rejected`

Traceability:
- preserves: `pendingsettlement`, `nooverdraft`
- scenarios: `insufficientBalanceScenario`
