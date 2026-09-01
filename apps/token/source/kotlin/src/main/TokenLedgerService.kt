interface TokenLedgerService {
    fun deposit(request: DepositRequest): DepositResult

    fun transfer(request: TransferRequest): TransferResult

    fun requestWithdrawal(request: WithdrawalRequest): PendingWithdrawal

    fun settleWithdrawal(request: SettleWithdrawalRequest): SettleWithdrawalResult

    fun rejectWithdrawal(request: RejectWithdrawalRequest): RejectWithdrawalResult
}
