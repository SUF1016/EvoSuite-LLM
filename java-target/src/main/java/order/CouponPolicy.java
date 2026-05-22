package order;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.Objects;

public class CouponPolicy {
    public boolean isApplicable(Coupon coupon, CustomerProfile customer, BigDecimal subtotal, LocalDate today) {
        return rejectionReason(coupon, customer, subtotal, today).isEmpty();
    }

    public String rejectionReason(Coupon coupon, CustomerProfile customer, BigDecimal subtotal, LocalDate today) {
        if (coupon == null) {
            return "NO_COUPON";
        }
        Objects.requireNonNull(customer, "customer");
        Objects.requireNonNull(subtotal, "subtotal");
        Objects.requireNonNull(today, "today");
        if (subtotal.signum() < 0) {
            throw new IllegalArgumentException("subtotal must be non-negative");
        }
        if (today.isAfter(coupon.getExpiresOn())) {
            return "EXPIRED";
        }
        if (subtotal.compareTo(coupon.getMinimumSubtotal()) < 0) {
            return "MINIMUM_NOT_REACHED";
        }
        if (coupon.isFirstOrderOnly() && !customer.isFirstOrder()) {
            return "FIRST_ORDER_ONLY";
        }
        if (coupon.getType() == CouponType.PERCENT && coupon.getAmount().compareTo(new BigDecimal("50.00")) > 0
            && !customer.isVip()) {
            return "HIGH_PERCENT_REQUIRES_VIP";
        }
        return "";
    }

    public BigDecimal discountFor(Coupon coupon, BigDecimal subtotal) {
        if (coupon == null) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        Objects.requireNonNull(subtotal, "subtotal");
        if (subtotal.signum() < 0) {
            throw new IllegalArgumentException("subtotal must be non-negative");
        }
        if (coupon.getType() == CouponType.FREE_SHIPPING) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        if (coupon.getType() == CouponType.FIXED) {
            return money(coupon.getAmount().min(subtotal));
        }
        BigDecimal percent = coupon.getAmount().divide(new BigDecimal("100"), 4, RoundingMode.HALF_UP);
        BigDecimal discount = subtotal.multiply(percent);
        BigDecimal cap = subtotal.multiply(new BigDecimal("0.50"));
        return money(discount.min(cap));
    }

    private static BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }
}
