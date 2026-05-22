package order;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class CheckoutCalculator {
    private final CouponPolicy couponPolicy;

    public CheckoutCalculator() {
        this(new CouponPolicy());
    }

    public CheckoutCalculator(CouponPolicy couponPolicy) {
        this.couponPolicy = Objects.requireNonNull(couponPolicy, "couponPolicy");
    }

    public CheckoutResult checkout(CheckoutRequest request, LocalDate today) {
        Objects.requireNonNull(request, "request");
        Objects.requireNonNull(today, "today");

        BigDecimal subtotal = subtotal(request);
        BigDecimal tierDiscount = tierDiscount(request.getCustomer(), subtotal);
        BigDecimal couponDiscount = BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        boolean couponApplied = false;
        List<String> messages = new ArrayList<String>();

        Coupon coupon = request.getCoupon();
        if (coupon != null) {
            String reason = couponPolicy.rejectionReason(coupon, request.getCustomer(), subtotal, today);
            if (reason.isEmpty()) {
                BigDecimal proposedCouponDiscount = couponPolicy.discountFor(coupon, subtotal);
                if (coupon.isStackable()) {
                    couponDiscount = proposedCouponDiscount;
                } else if (proposedCouponDiscount.compareTo(tierDiscount) > 0) {
                    messages.add("TIER_DISCOUNT_REPLACED");
                    tierDiscount = BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
                    couponDiscount = proposedCouponDiscount;
                } else {
                    messages.add("COUPON_NOT_BETTER_THAN_TIER");
                }
                couponApplied = coupon.getType() == CouponType.FREE_SHIPPING
                    || couponDiscount.compareTo(BigDecimal.ZERO) > 0;
            } else if (!"NO_COUPON".equals(reason)) {
                messages.add(reason);
            }
        }

        BigDecimal combinedDiscount = capDiscount(subtotal, tierDiscount.add(couponDiscount));
        BigDecimal discountedSubtotal = subtotal.subtract(combinedDiscount);
        BigDecimal shippingFee = shippingFee(request, discountedSubtotal, couponApplied);
        BigDecimal tax = tax(discountedSubtotal.add(shippingFee), request.getCustomer().getRegion());
        BigDecimal total = money(discountedSubtotal.add(shippingFee).add(tax));

        return new CheckoutResult(
            subtotal,
            tierDiscount,
            couponDiscount,
            shippingFee,
            tax,
            total,
            couponApplied,
            messages
        );
    }

    public BigDecimal subtotal(CheckoutRequest request) {
        Objects.requireNonNull(request, "request");
        BigDecimal subtotal = BigDecimal.ZERO;
        for (OrderItem item : request.getItems()) {
            subtotal = subtotal.add(item.lineTotal());
        }
        return money(subtotal);
    }

    public BigDecimal tierDiscount(CustomerProfile customer, BigDecimal subtotal) {
        Objects.requireNonNull(customer, "customer");
        Objects.requireNonNull(subtotal, "subtotal");
        if (subtotal.signum() < 0) {
            throw new IllegalArgumentException("subtotal must be non-negative");
        }
        if (customer.isVip()) {
            return money(subtotal.multiply(new BigDecimal("0.10")).min(new BigDecimal("40.00")));
        }
        if (customer.isLoyalMember()) {
            return money(subtotal.multiply(new BigDecimal("0.05")).min(new BigDecimal("25.00")));
        }
        return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
    }

    private BigDecimal shippingFee(CheckoutRequest request, BigDecimal discountedSubtotal, boolean couponApplied) {
        if (allItemsDigital(request)) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        Coupon coupon = request.getCoupon();
        if (couponApplied && coupon != null && coupon.getType() == CouponType.FREE_SHIPPING) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        if (discountedSubtotal.compareTo(new BigDecimal("120.00")) >= 0) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        if (request.getCustomer().isVip() && !request.isExpeditedShipping()) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }

        BigDecimal base = "INTL".equals(request.getCustomer().getRegion())
            ? new BigDecimal("24.99")
            : new BigDecimal("6.99");
        if (request.isExpeditedShipping()) {
            base = base.add(new BigDecimal("9.99"));
        }
        return money(base);
    }

    private BigDecimal tax(BigDecimal taxableAmount, String region) {
        if ("EU".equals(region)) {
            return money(taxableAmount.multiply(new BigDecimal("0.20")));
        }
        if ("US".equals(region)) {
            return money(taxableAmount.multiply(new BigDecimal("0.07")));
        }
        return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
    }

    private boolean allItemsDigital(CheckoutRequest request) {
        for (OrderItem item : request.getItems()) {
            if (!item.isDigital()) {
                return false;
            }
        }
        return true;
    }

    private BigDecimal capDiscount(BigDecimal subtotal, BigDecimal requestedDiscount) {
        BigDecimal maximumDiscount = subtotal.multiply(new BigDecimal("0.70"));
        return money(requestedDiscount.min(maximumDiscount));
    }

    private static BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }
}
