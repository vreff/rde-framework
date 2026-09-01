# Scenario Test Templates

This template maps Clafer scenarios to code-level tests.

## successfulDepositScenario

Requirements:
- `nooverdraft`
- `balanceconsistency`

Given:
- account A exists with balance B >= 0
- deposit amount D > 0

When:
- call `deposit(accountId=A, amount=D)`

Then:
- afterBalance = B + D
- afterBalance >= 0
- total supply reflects updated balances

## successfulTransferScenario

Requirements:
- `transfervalidity`
- `singlesource`
- `balanceconsistency`
- `nooverdraft`

Given:
- sender S and receiver R are valid accounts
- senderBefore >= amount > 0
- receiverBefore >= 0

When:
- call `transfer(sender=S, receiver=R, amount=A)`

Then:
- senderAfter = senderBefore - A
- receiverAfter = receiverBefore + A
- senderAfter >= 0
- senderBefore + receiverBefore = senderAfter + receiverAfter
- total supply unchanged by transfer operation

## insufficientBalanceScenario

Requirements:
- `nooverdraft`

Given:
- senderBefore >= 0
- attemptedWithdrawalAmount > senderBefore
- pending withdrawal exists for account

When:
- call `rejectWithdrawal` after review

Then:
- senderAfter = senderBefore
- pending withdrawal status becomes `REJECTED`

## pendingWithdrawalSettlementScenario

Requirements:
- `pendingsettlement`
- `balanceconsistency`
- `nooverdraft`

Given:
- pending withdrawal exists with amount W > 0
- account balance before >= W

When:
- call `settleWithdrawal(withdrawalId)`

Then:
- balanceAfter = balanceBefore - W
- balanceAfter >= 0
- pending withdrawal status becomes `SETTLED`

## invalidTransferScenario

Requirements:
- `transfervalidity`

Given:
- sender or receiver is invalid

When:
- call `transfer(sender, receiver, amount)`

Then:
- operation is rejected
- no debit or credit is applied
