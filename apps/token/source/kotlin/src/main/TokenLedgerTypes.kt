enum class WithdrawalStatus {
    PENDING,
    SETTLED,
    REJECTED
}

data class AccountState(
    val accountId: String,
    val balance: Long
)

data class DepositRequest(
    val accountId: String,
    val amount: Long
)

data class DepositResult(
    val beforeBalance: Long,
    val afterBalance: Long,
    val totalSupplyAfter: Long
)

data class TransferRequest(
    val senderId: String,
    val receiverId: String,
    val amount: Long
)

data class TransferResult(
    val senderBefore: Long,
    val senderAfter: Long,
    val receiverBefore: Long,
    val receiverAfter: Long,
    val totalSupplyAfter: Long
)

data class WithdrawalRequest(
    val accountId: String,
    val amount: Long
)

data class PendingWithdrawal(
    val withdrawalId: String,
    val accountId: String,
    val amount: Long,
    val status: WithdrawalStatus
)

data class SettleWithdrawalRequest(
    val withdrawalId: String
)

data class SettleWithdrawalResult(
    val beforeBalance: Long,
    val afterBalance: Long,
    val status: WithdrawalStatus
)

data class RejectWithdrawalRequest(
    val withdrawalId: String,
    val reason: String
)

data class RejectWithdrawalResult(
    val beforeBalance: Long,
    val afterBalance: Long,
    val status: WithdrawalStatus
)
