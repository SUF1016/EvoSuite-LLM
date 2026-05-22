package order;

import java.util.Objects;

public class CustomerProfile {
    private final CustomerTier tier;
    private final int loyaltyPoints;
    private final boolean firstOrder;
    private final String region;

    public CustomerProfile(CustomerTier tier, int loyaltyPoints, boolean firstOrder, String region) {
        this.tier = Objects.requireNonNull(tier, "tier");
        if (loyaltyPoints < 0) {
            throw new IllegalArgumentException("loyaltyPoints must be non-negative");
        }
        this.loyaltyPoints = loyaltyPoints;
        this.firstOrder = firstOrder;
        this.region = normalizeRegion(region);
    }

    public CustomerTier getTier() {
        return tier;
    }

    public int getLoyaltyPoints() {
        return loyaltyPoints;
    }

    public boolean isFirstOrder() {
        return firstOrder;
    }

    public String getRegion() {
        return region;
    }

    public boolean isVip() {
        return tier == CustomerTier.VIP;
    }

    public boolean isLoyalMember() {
        return tier == CustomerTier.MEMBER && loyaltyPoints >= 1000;
    }

    private String normalizeRegion(String value) {
        if (value == null || value.trim().isEmpty()) {
            return "US";
        }
        return value.trim().toUpperCase();
    }
}
