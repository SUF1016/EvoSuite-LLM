package order;

import org.junit.Test;
import static org.junit.Assert.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Collections;
import java.util.List;

public class CouponPolicyLLMEnhancedTest {

    private static final LocalDate TODAY = LocalDate.of(2023, 10, 15);
    private static final LocalDate VALID_DATE = LocalDate.of(2024, 12, 31);

    private CustomerProfile createCustomer(boolean isFirstOrder, boolean isVip) {
        return new CustomerProfile(isVip ? CustomerTier.VIP : CustomerTier.GUEST, 0, isFirstOrder, "US");
    }

    @Test
    public void testRejectionReason_Boundary_MinimumSubtotal() {
        // Kills ConditionalsBoundaryMutator and NegateConditionalsMutator in rejectionReason
        CouponPolicy policy = new CouponPolicy();
        BigDecimal minSubtotal = new BigDecimal("50.00");
        Coupon coupon = new Coupon("MIN", CouponType.FIXED, new BigDecimal("5.00"), minSubtotal, VALID_DATE, false, false);
        CustomerProfile customer = createCustomer(true, false);

        // Exactly at minimum (should be valid)
        String reasonAtMin = policy.rejectionReason(coupon, customer, minSubtotal, TODAY);
        assertEquals("", reasonAtMin);

        // Just below minimum (should be rejected)
        String reasonBelowMin = policy.rejectionReason(coupon, customer, minSubtotal.subtract(new BigDecimal("0.01")), TODAY);
        assertEquals("MINIMUM_NOT_REACHED", reasonBelowMin);
    }

    @Test
    public void testRejectionReason_HighPercentRequiresVip() {
        // Kills branch polarity mutant for VIP check
        Coupon highPercentCoupon = new Coupon("HIGH", CouponType.PERCENT, new BigDecimal("55.00"), BigDecimal.ZERO, VALID_DATE, false, false);
        CustomerProfile nonVip = createCustomer(true, false);
        CustomerProfile vip = createCustomer(true, true);
        CouponPolicy policy = new CouponPolicy();

        // Non-VIP should be rejected
        String reasonNonVip = policy.rejectionReason(highPercentCoupon, nonVip, new BigDecimal("100.00"), TODAY);
        assertEquals("HIGH_PERCENT_REQUIRES_VIP", reasonNonVip);

        // VIP should be accepted
        String reasonVip = policy.rejectionReason(highPercentCoupon, vip, new BigDecimal("100.00"), TODAY);
        assertEquals("", reasonVip);
        
        // 50% exactly should be allowed for non-VIP (boundary)
        Coupon exactFifty = new Coupon("FIFTY", CouponType.PERCENT, new BigDecimal("50.00"), BigDecimal.ZERO, VALID_DATE, false, false);
        String reasonFifty = policy.rejectionReason(exactFifty, nonVip, new BigDecimal("100.00"), TODAY);
        assertEquals("", reasonFifty);
    }

    @Test
    public void testDiscountFor_FixedAmountCap() {
        // Kills return oracle mutant: ensures min logic is active
        CouponPolicy policy = new CouponPolicy();
        Coupon fixedCoupon = new Coupon("FIX", CouponType.FIXED, new BigDecimal("20.00"), BigDecimal.ZERO, VALID_DATE, false, false);

        // Subtotal > Amount -> Discount is Amount
        BigDecimal discount1 = policy.discountFor(fixedCoupon, new BigDecimal("100.00"));
        assertEquals(new BigDecimal("20.00"), discount1);

        // Subtotal < Amount -> Discount is Subtotal
        BigDecimal discount2 = policy.discountFor(fixedCoupon, new BigDecimal("15.00"));
        assertEquals(new BigDecimal("15.00"), discount2);
    }

    @Test
    public void testDiscountFor_PercentCap() {
        // Kills return oracle mutant: ensures 50% cap logic is active
        CouponPolicy policy = new CouponPolicy();
        // 60% coupon, but capped at 50% of subtotal
        Coupon highPercent = new Coupon("PCT", CouponType.PERCENT, new BigDecimal("60.00"), BigDecimal.ZERO, VALID_DATE, false, false);
        
        BigDecimal subtotal = new BigDecimal("100.00");
        BigDecimal discount = policy.discountFor(highPercent, subtotal);
        
        // 60% of 100 is 60, but cap is 50% of 100 which is 50.
        assertEquals(new BigDecimal("50.00"), discount);
    }

    @Test
    public void testCheckout_NonStackableCouponReplacesTier() {
        // Integration test killing mutants in CheckoutCalculator regarding stackable/replacement logic
        CouponPolicy policy = new CouponPolicy();
        CheckoutCalculator calculator = new CheckoutCalculator(policy);

        // VIP Customer: 10% tier discount
        CustomerProfile vip = createCustomer(false, true);
        
        // Fixed $15 coupon. 
        // Subtotal $100. Tier discount = $10. Coupon discount = $15.
        // Coupon is NOT stackable. Coupon > Tier.
        // Expected: Tier becomes 0, Coupon becomes 15.
        Coupon nonStackable = new Coupon("NS", CouponType.FIXED, new BigDecimal("15.00"), BigDecimal.ZERO, VALID_DATE, false, false);
        
        OrderItem item = new OrderItem("SKU1", 1, new BigDecimal("100.00"), false, "General");
        List<OrderItem> items = Collections.singletonList(item);
        CheckoutRequest request = new CheckoutRequest(items, vip, nonStackable, false);

        CheckoutResult result = calculator.checkout(request, TODAY);

        assertEquals(new BigDecimal("0.00"), result.getTierDiscount());
        assertEquals(new BigDecimal("15.00"), result.getCouponDiscount());
        assertFalse(result.getMessages().contains("COUPON_NOT_BETTER_THAN_TIER"));
        assertTrue(result.getMessages().contains("TIER_DISCOUNT_REPLACED"));
        
        // Total check:
        // Subtotal: 100
        // Discount: 15
        // Discounted Subtotal: 85
        // Shipping: 0 (VIP, not expedited)
        // Tax (US 7%): 85 * 0.07 = 5.95
        // Total: 85 + 5.95 = 90.95
        assertEquals(new BigDecimal("90.95"), result.getTotal());
    }

    @Test
    public void testCheckout_AllDigitalItemsFreeShipping() {
        // Kills survived mutants in allItemsDigital and shippingFee logic
        CouponPolicy policy = new CouponPolicy();
        CheckoutCalculator calculator = new CheckoutCalculator(policy);

        CustomerProfile guest = createCustomer(false, false);
        
        // Digital item
        OrderItem digitalItem = new OrderItem("DIG1", 1, new BigDecimal("50.00"), true, "Software");
        List<OrderItem> items = Collections.singletonList(digitalItem);
        
        // No coupon, but shipping should be 0 because all items are digital
        CheckoutRequest request = new CheckoutRequest(items, guest, null, false);
        
        CheckoutResult result = calculator.checkout(request, TODAY);
        
        assertEquals(new BigDecimal("0.00"), result.getShippingFee());
        // Tax on 50.00 (US 7%) = 3.50
        assertEquals(new BigDecimal("53.50"), result.getTotal());
    }
}
