package order;

import org.junit.Test;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.Assert.*;

public class CheckoutCalculatorLLMEnhancedTest {

    private static final LocalDate TODAY = LocalDate.of(2023, 1, 1);
    private static final LocalDate FUTURE = TODAY.plusDays(10);

    // Helper to create a standard physical item
    private OrderItem physicalItem(String sku, BigDecimal price) {
        return new OrderItem(sku, 1, price, false, "General");
    }

    // Helper to create a standard digital item
    private OrderItem digitalItem(String sku, BigDecimal price) {
        return new OrderItem(sku, 1, price, true, "Digital");
    }

    // Helper to create customer
    private CustomerProfile createCustomer(boolean firstOrder, boolean vip) {
        return new CustomerProfile(vip ? CustomerTier.VIP : CustomerTier.GUEST, 0, firstOrder, "US");
    }

    /**
     * Kills mutants in allItemsDigital (return-oracle, branch-polarity).
     * Verifies that shipping is free ONLY if ALL items are digital.
     * Mutants: replaced boolean return with false/true, negated conditional.
     */
    @Test
    public void testShipping_FreeForAllDigitalItems() {
        CheckoutCalculator calculator = new CheckoutCalculator();
        
        // Case 1: All digital -> Free shipping
        List<OrderItem> allDigital = Arrays.asList(
            digitalItem("D1", new BigDecimal("10.00")),
            digitalItem("D2", new BigDecimal("20.00"))
        );
        CustomerProfile guest = createCustomer(false, false);
        CheckoutRequest reqAllDigital = new CheckoutRequest(allDigital, guest, null, false);
        CheckoutResult resAllDigital = calculator.checkout(reqAllDigital, TODAY);
        
        assertEquals(new BigDecimal("0.00"), resAllDigital.getShippingFee());

        // Case 2: Mixed items -> Standard shipping applies ($6.99 for US Guest)
        List<OrderItem> mixed = Arrays.asList(
            digitalItem("D1", new BigDecimal("10.00")),
            physicalItem("P1", new BigDecimal("20.00"))
        );
        CheckoutRequest reqMixed = new CheckoutRequest(mixed, guest, null, false);
        CheckoutResult resMixed = calculator.checkout(reqMixed, TODAY);
        
        assertEquals(new BigDecimal("6.99"), resMixed.getShippingFee());
    }

    /**
     * Kills boundary mutant in checkout (ConditionalsBoundaryMutator at line 38/47 logic) 
     * and shippingFee (ConditionalsBoundaryMutator at line 102).
     * 
     * Specifically tests the $120.00 threshold for free shipping.
     * Rule: Shipping is free if discountedSubtotal >= 120.00.
     */
    @Test
    public void testShipping_FreeThresholdBoundary() {
        CheckoutCalculator calculator = new CheckoutCalculator();
        CustomerProfile guest = createCustomer(false, false);

        // Case 1: Discounted Subtotal exactly 120.00 -> Free Shipping
        // We need subtotal such that after tier discount (0 for guest), it is 120.
        OrderItem itemExact = physicalItem("P1", new BigDecimal("120.00"));
        CheckoutRequest reqExact = new CheckoutRequest(Collections.singletonList(itemExact), guest, null, false);
        CheckoutResult resExact = calculator.checkout(reqExact, TODAY);
        
        assertEquals(new BigDecimal("120.00"), resExact.getSubtotal());
        assertEquals(new BigDecimal("0.00"), resExact.getShippingFee()); // Boundary hit

        // Case 2: Discounted Subtotal 119.99 -> Paid Shipping
        OrderItem itemBelow = physicalItem("P2", new BigDecimal("119.99"));
        CheckoutRequest reqBelow = new CheckoutRequest(Collections.singletonList(itemBelow), guest, null, false);
        CheckoutResult resBelow = calculator.checkout(reqBelow, TODAY);
        
        assertEquals(new BigDecimal("119.99"), resBelow.getSubtotal());
        assertEquals(new BigDecimal("6.99"), resBelow.getShippingFee()); // Boundary missed
    }

    /**
     * Kills branch-polarity mutants in checkout regarding coupon application logic.
     * Tests: Non-stackable coupon that is NOT better than tier discount.
     * Rule: If !stackable && couponDiscount <= tierDiscount, ignore coupon, keep tier.
     */
    @Test
    public void testCoupon_NonStackableNotBetterThanTier() {
        CheckoutCalculator calculator = new CheckoutCalculator();
        
        // VIP gets 10% tier discount. On $100, that's $10.
        CustomerProfile vip = createCustomer(false, true);
        
        // Coupon: Fixed $5. Not stackable.
        // $5 < $10, so coupon should be rejected in favor of tier.
        Coupon weakCoupon = new Coupon("WEAK", CouponType.FIXED, new BigDecimal("5.00"), BigDecimal.ZERO, FUTURE, false, false);
        
        OrderItem item = physicalItem("P1", new BigDecimal("100.00"));
        CheckoutRequest request = new CheckoutRequest(Collections.singletonList(item), vip, weakCoupon, false);
        
        CheckoutResult result = calculator.checkout(request, TODAY);

        // Tier discount should remain
        assertEquals(new BigDecimal("10.00"), result.getTierDiscount());
        // Coupon discount should be zero
        assertEquals(new BigDecimal("0.00"), result.getCouponDiscount());
        // Message should indicate it wasn't better
        assertTrue(result.getMessages().contains("COUPON_NOT_BETTER_THAN_TIER"));
        assertFalse(result.isCouponApplied());
    }

    /**
     * Kills branch-polarity mutants in checkout regarding stackable coupons.
     * Tests: Stackable coupon applies ON TOP of tier discount.
     */
    @Test
    public void testCoupon_StackableAppliesWithTier() {
        CheckoutCalculator calculator = new CheckoutCalculator();
        
        // VIP gets 10% tier discount. On $100, that's $10.
        CustomerProfile vip = createCustomer(false, true);
        
        // Coupon: Fixed $15. Stackable.
        Coupon stackableCoupon = new Coupon("STACK", CouponType.FIXED, new BigDecimal("15.00"), BigDecimal.ZERO, FUTURE, false, true);
        
        OrderItem item = physicalItem("P1", new BigDecimal("100.00"));
        CheckoutRequest request = new CheckoutRequest(Collections.singletonList(item), vip, stackableCoupon, false);
        
        CheckoutResult result = calculator.checkout(request, TODAY);

        // Both discounts should apply
        assertEquals(new BigDecimal("10.00"), result.getTierDiscount());
        assertEquals(new BigDecimal("15.00"), result.getCouponDiscount());
        
        // Total Discount = 25.00
        // Discounted Subtotal = 75.00
        // Shipping = 0 (VIP)
        // Tax (US 7%) = 75 * 0.07 = 5.25
        // Total = 80.25
        assertEquals(new BigDecimal("80.25"), result.getTotal());
        assertTrue(result.isCouponApplied());
    }

    /**
     * Kills branch-polarity mutants in checkout regarding rejection reasons.
     * Tests: Expired coupon results in "EXPIRED" message and no discount.
     */
    @Test
    public void testCoupon_RejectedWhenExpired() {
        CheckoutCalculator calculator = new CheckoutCalculator();
        CustomerProfile guest = createCustomer(false, false);
        
        // Coupon expired yesterday
        LocalDate expiredDate = TODAY.minusDays(1);
        Coupon expiredCoupon = new Coupon("EXP", CouponType.FIXED, new BigDecimal("10.00"), BigDecimal.ZERO, expiredDate, false, false);
        
        OrderItem item = physicalItem("P1", new BigDecimal("50.00"));
        CheckoutRequest request = new CheckoutRequest(Collections.singletonList(item), guest, expiredCoupon, false);
        
        CheckoutResult result = calculator.checkout(request, TODAY);

        assertEquals(new BigDecimal("0.00"), result.getCouponDiscount());
        assertEquals(new BigDecimal("0.00"), result.getTierDiscount());
        assertTrue(result.getMessages().contains("EXPIRED"));
        assertFalse(result.isCouponApplied());
    }

    /**
     * Kills boundary mutant in shippingFee (NegateConditionalsMutator / ConditionalsBoundaryMutator).
     * Tests: VIP shipping logic.
     * Rule: VIPs get free shipping UNLESS expedited is requested.
     */
    @Test
    public void testShipping_VipExpeditedBoundary() {
        CheckoutCalculator calculator = new CheckoutCalculator();
        CustomerProfile vip = createCustomer(false, true);
        OrderItem item = physicalItem("P1", new BigDecimal("50.00")); // Below $120 threshold

        // Case 1: VIP, Standard Shipping -> Free
        CheckoutRequest reqStandard = new CheckoutRequest(Collections.singletonList(item), vip, null, false);
        CheckoutResult resStandard = calculator.checkout(reqStandard, TODAY);
        assertEquals(new BigDecimal("0.00"), resStandard.getShippingFee());

        // Case 2: VIP, Expedited Shipping -> Paid
        CheckoutRequest reqExpedited = new CheckoutRequest(Collections.singletonList(item), vip, null, true);
        CheckoutResult resExpedited = calculator.checkout(reqExpedited, TODAY);
        // Base $6.99 + Expedited $9.99 = $16.98
        assertEquals(new BigDecimal("16.98"), resExpedited.getShippingFee());
    }
}
