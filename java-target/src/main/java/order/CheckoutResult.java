package order;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class CheckoutResult {
    private final BigDecimal subtotal;
    private final BigDecimal tierDiscount;
    private final BigDecimal couponDiscount;
    private final BigDecimal shippingFee;
    private final BigDecimal tax;
    private final BigDecimal total;
    private final boolean couponApplied;
    private final List<String> messages;

    public CheckoutResult(
        BigDecimal subtotal,
        BigDecimal tierDiscount,
        BigDecimal couponDiscount,
        BigDecimal shippingFee,
        BigDecimal tax,
        BigDecimal total,
        boolean couponApplied,
        List<String> messages
    ) {
        this.subtotal = subtotal;
        this.tierDiscount = tierDiscount;
        this.couponDiscount = couponDiscount;
        this.shippingFee = shippingFee;
        this.tax = tax;
        this.total = total;
        this.couponApplied = couponApplied;
        this.messages = Collections.unmodifiableList(new ArrayList<String>(messages));
    }

    public BigDecimal getSubtotal() {
        return subtotal;
    }

    public BigDecimal getTierDiscount() {
        return tierDiscount;
    }

    public BigDecimal getCouponDiscount() {
        return couponDiscount;
    }

    public BigDecimal getShippingFee() {
        return shippingFee;
    }

    public BigDecimal getTax() {
        return tax;
    }

    public BigDecimal getTotal() {
        return total;
    }

    public boolean isCouponApplied() {
        return couponApplied;
    }

    public List<String> getMessages() {
        return messages;
    }
}
