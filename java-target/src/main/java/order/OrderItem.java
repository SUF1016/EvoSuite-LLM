package order;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public class OrderItem {
    private final String sku;
    private final int quantity;
    private final BigDecimal unitPrice;
    private final boolean digital;
    private final String category;

    public OrderItem(String sku, int quantity, BigDecimal unitPrice, boolean digital, String category) {
        this.sku = requireText(sku, "sku");
        if (quantity <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
        this.quantity = quantity;
        this.unitPrice = money(Objects.requireNonNull(unitPrice, "unitPrice"));
        if (this.unitPrice.signum() < 0) {
            throw new IllegalArgumentException("unitPrice must be non-negative");
        }
        this.digital = digital;
        this.category = requireText(category, "category");
    }

    public String getSku() {
        return sku;
    }

    public int getQuantity() {
        return quantity;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }

    public boolean isDigital() {
        return digital;
    }

    public String getCategory() {
        return category;
    }

    public BigDecimal lineTotal() {
        return money(unitPrice.multiply(new BigDecimal(quantity)));
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
