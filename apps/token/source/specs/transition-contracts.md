# Transition Contracts (From Clafer)

This document maps Clafer transition components to code-level contracts.

## Transfer Transition

Clafer components:
- `BalanceTransitionUpdate`
- `BalanceTransitionPrecondition`
- `BalanceTransitionInvariant`

Contract:
- Inputs: `transferAmount`, `senderBefore`, `receiverBefore`
- Update equations:
  - `senderAfter = senderBefore - transferAmount`
  - `receiverAfter = receiverBefore + transferAmount`
- Preconditions:
  - `transferAmount > 0`
- Invariants:
  - `senderBefore >= 0`
  - `receiverBefore >= 0`
  - `senderAfter >= 0`
  - `senderBefore + receiverBefore = senderAfter + receiverAfter`

## Deposit Transition

Clafer components:
- `DepositTransitionUpdate`
- `DepositTransitionPrecondition`
- `DepositTransitionInvariant`

Contract:
- Inputs: `depositAmount`, `balanceBefore`
- Update equation:
  - `balanceAfter = balanceBefore + depositAmount`
- Preconditions:
  - `depositAmount > 0`
- Invariants:
  - `balanceBefore >= 0`
  - `balanceAfter >= 0`

## Withdrawal Transition

Clafer components:
- `WithdrawalTransitionUpdate`
- `WithdrawalTransitionPrecondition`
- `WithdrawalTransitionInvariant`

Contract:
- Inputs: `withdrawalAmount`, `balanceBefore`
- Update equation:
  - `balanceAfter = balanceBefore - withdrawalAmount`
- Preconditions:
  - `withdrawalAmount > 0`
  - `withdrawalAmount <= balanceBefore`
- Invariants:
  - `balanceBefore >= 0`
  - `balanceAfter >= 0`

## Event Wiring Expectations

- `applyTransferLedgerUpdateEvent` executes transfer update and enforces transfer precondition + invariant
- `depositEvent` executes deposit update and enforces deposit precondition + invariant
- `settleEvent` executes withdrawal update and enforces withdrawal precondition + invariant
