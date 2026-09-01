import java.util.UUID

class InMemoryTokenLedgerService(
    initialBalances: Map<String, Long> = emptyMap()
) : TokenLedgerService {

    private val balances: MutableMap<String, Long> = initialBalances.toMutableMap()
    private val pending: MutableMap<String, PendingWithdrawal> = mutableMapOf()

    override fun deposit(request: DepositRequest): DepositResult {
        require(request.amount > 0) { "deposit amount must be > 0" }

        val before = balanceOf(request.accountId)
        val after = before + request.amount
        require(after >= 0) { "deposit overflow/underflow invalid" }

        balances[request.accountId] = after
        val supply = totalSupply()

        return DepositResult(before, after, supply)
    }

    override fun transfer(request: TransferRequest): TransferResult {
        require(request.amount > 0) { "transfer amount must be > 0" }
        require(request.senderId != request.receiverId) { "sender and receiver must differ" }

        val senderBefore = balanceOf(request.senderId)
        val receiverBefore = balanceOf(request.receiverId)

        require(senderBefore >= request.amount) { "insufficient balance" }

        val senderAfter = senderBefore - request.amount
        val receiverAfter = receiverBefore + request.amount

        require(senderAfter >= 0) { "sender balance must remain non-negative" }
        require(senderBefore + receiverBefore == senderAfter + receiverAfter) {
            "transfer must conserve value"
        }

        balances[request.senderId] = senderAfter
        balances[request.receiverId] = receiverAfter

        val supply = totalSupply()
        return TransferResult(senderBefore, senderAfter, receiverBefore, receiverAfter, supply)
    }

    override fun requestWithdrawal(request: WithdrawalRequest): PendingWithdrawal {
        require(request.amount > 0) { "withdrawal amount must be > 0" }

        val id = UUID.randomUUID().toString()
        val record = PendingWithdrawal(
            withdrawalId = id,
            accountId = request.accountId,
            amount = request.amount,
            status = WithdrawalStatus.PENDING
        )

        pending[id] = record
        return record
    }

    override fun settleWithdrawal(request: SettleWithdrawalRequest): SettleWithdrawalResult {
        val record = pending[request.withdrawalId]
            ?: error("unknown withdrawal id: ${request.withdrawalId}")

        require(record.status == WithdrawalStatus.PENDING) { "withdrawal is not pending" }

        val before = balanceOf(record.accountId)
        require(record.amount <= before) { "withdrawal exceeds account balance" }

        val after = before - record.amount
        require(after >= 0) { "settlement must keep balance non-negative" }

        balances[record.accountId] = after
        pending[record.withdrawalId] = record.copy(status = WithdrawalStatus.SETTLED)

        return SettleWithdrawalResult(before, after, WithdrawalStatus.SETTLED)
    }

    override fun rejectWithdrawal(request: RejectWithdrawalRequest): RejectWithdrawalResult {
        val record = pending[request.withdrawalId]
            ?: error("unknown withdrawal id: ${request.withdrawalId}")

        require(record.status == WithdrawalStatus.PENDING) { "withdrawal is not pending" }

        val before = balanceOf(record.accountId)
        val after = before

        pending[record.withdrawalId] = record.copy(status = WithdrawalStatus.REJECTED)

        return RejectWithdrawalResult(before, after, WithdrawalStatus.REJECTED)
    }

    private fun balanceOf(accountId: String): Long = balances[accountId] ?: 0L

    private fun totalSupply(): Long = balances.values.sum()
}
