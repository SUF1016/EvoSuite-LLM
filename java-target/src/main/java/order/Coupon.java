package order;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.Objects;

public class Coupon {
    private final String code;
    private final CouponType type;
    private final BigDecimal amount;
    private final BigDecimal minimumSubtotal;
    private final LocalDate expiresOn;
    private final boolean firstOrderOnly;
    private final boolean stackable;

    public Coupon(
        String code,
        CouponType type,
        BigDecimal amount,
        BigDecimal minimumSubtotal,
        LocalDate expiresOn,
        boolean firstOrderOnly,
        boolean stackable
    ) {
        this.code = requireText(code, "code").toUpperCase();
        this.type = Objects.requireNonNull(type, "type");
        this.amount = money(Objects.requireNonNull(amount, "amount"));
        this.minimumSubtotal = money(Objects.requireNonNull(minimumSubtotal, "minimumSubtotal"));
        this.expiresOn = Objects.requireNonNull(expiresOn, "expiresOn");
        this.firstOrderOnly = firstOrderOnly;
        this.stackable = stackable;
        validate();
    }

    public String getCode() {
        return code;
    }

    public CouponType getType() {
        return type;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public BigDecimal getMinimumSubtotal() {
        return minimumSubtotal;
    }

    public LocalDate getExpiresOn() {
        return expiresOn;
    }

    public boolean isFirstOrderOnly() {
        return firstOrderOnly;
    }

    public boolean isStackable() {
        return stackable;
    }

    private void validate() {
        if (minimumSubtotal.signum() < 0) {
            throw new IllegalArgumentException("minimumSubtotal must be non-negative");
        }
        if (type == CouponType.PERCENT) {
            if (amount.compareTo(BigDecimal.ONE) < 0 || amount.compareTo(new BigDecimal("60.00")) > 0) {
                throw new IllegalArgumentException("percent coupon must be between 1 and 60");
            }
        } else if (type == CouponType.FIXED) {
            if (amount.signum() <= 0) {
                throw new IllegalArgumentException("fixed coupon amount must be positive");
            }
        } else if (type == CouponType.FREE_SHIPPING) {
            if (amount.compareTo(BigDecimal.ZERO) != 0) {
                throw new IllegalArgumentException("free shipping coupon amount must be zero");
            }
        }
    }

    private static String requireText(String value, String name) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException(name + " must not be blank");
        }
        return value.trim();
    }

    private static BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }
}
