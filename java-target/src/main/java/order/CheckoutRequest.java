package order;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class CheckoutRequest {
    private final List<OrderItem> items;
    private final CustomerProfile customer;
    private final Coupon coupon;
    private final boolean expeditedShipping;

    public CheckoutRequest(List<OrderItem> items, CustomerProfile customer, Coupon coupon, boolean expeditedShipping) {
        Objects.requireNonNull(items, "items");
        if (items.isEmpty()) {
            throw new IllegalArgumentException("order must contain at least one item");
        }
        this.items = Collections.unmodifiableList(new ArrayList<OrderItem>(items));
        this.customer = Objects.requireNonNull(customer, "customer");
        this.coupon = coupon;
        this.expeditedShipping = expeditedShipping;
    }

    public List<OrderItem> getItems() {
        return items;
    }

    public CustomerProfile getCustomer() {
        return customer;
    }

    public Coupon getCoupon() {
        return coupon;
    }

    public boolean isExpeditedShipping() {
        return expeditedShipping;
    }
}
