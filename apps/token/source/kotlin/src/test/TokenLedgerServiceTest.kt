import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class TokenLedgerServiceTest {

    @Test
    fun successfulDepositScenario_updatesBalanceAndSupply() {
        val service = InMemoryTokenLedgerService(mapOf("alice" to 100L))

        val result = service.deposit(DepositRequest(accountId = "alice", amount = 25L))

        assertEquals(100L, result.beforeBalance)
        assertEquals(125L, result.afterBalance)
        assertEquals(125L, result.totalSupplyAfter)
    }

    @Test
    fun successfulTransferScenario_preservesConservationAndNoOverdraft() {
        val service = InMemoryTokenLedgerService(
            mapOf(
                "alice" to 100L,
                "bob" to 30L
            )
        )

        val result = service.transfer(
            TransferRequest(
                senderId = "alice",
                receiverId = "bob",
                amount = 40L
            )
        )

        assertEquals(100L, result.senderBefore)
        assertEquals(60L, result.senderAfter)
        assertEquals(30L, result.receiverBefore)
        assertEquals(70L, result.receiverAfter)
        assertEquals(130L, result.totalSupplyAfter)
        assertEquals(result.senderBefore + result.receiverBefore, result.senderAfter + result.receiverAfter)
    }

    @Test
    fun insufficientBalanceScenario_rejectsOverdrawAttempt() {
        val service = InMemoryTokenLedgerService(mapOf("alice" to 10L, "bob" to 5L))

        assertThrows(IllegalArgumentException::class.java) {
            service.transfer(TransferRequest(senderId = "alice", receiverId = "bob", amount = 20L))
        }
    }

    @Test
    fun pendingWithdrawalSettlementScenario_settlesPendingWithdrawal() {
        val service = InMemoryTokenLedgerService(mapOf("alice" to 100L))

        val pending = service.requestWithdrawal(WithdrawalRequest(accountId = "alice", amount = 40L))
        val settled = service.settleWithdrawal(SettleWithdrawalRequest(withdrawalId = pending.withdrawalId))

        assertEquals(100L, settled.beforeBalance)
        assertEquals(60L, settled.afterBalance)
        assertEquals(WithdrawalStatus.SETTLED, settled.status)
    }

    @Test
    fun invalidTransferScenario_rejectsSameAccountTransfer() {
        val service = InMemoryTokenLedgerService(mapOf("alice" to 100L))

        assertThrows(IllegalArgumentException::class.java) {
            service.transfer(TransferRequest(senderId = "alice", receiverId = "alice", amount = 1L))
        }
    }
}
