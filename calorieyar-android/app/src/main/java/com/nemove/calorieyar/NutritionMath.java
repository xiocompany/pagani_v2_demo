package com.nemove.calorieyar;

public final class NutritionMath {
    private NutritionMath() {}

    public static int foodCalories(FoodItem food, double amount) {
        return (int) Math.round(food.calories * Math.max(0, amount));
    }

    public static int activityCalories(double met, double weightKg, int minutes) {
        if (met <= 0 || weightKg <= 0 || minutes <= 0) return 0;
        return (int) Math.round(met * 3.5 * weightKg / 200.0 * minutes);
    }

    public static int mifflinStJeor(int age, double weightKg, double heightCm, boolean male, double activityFactor, int goalAdjustment) {
        double bmr = 10 * weightKg + 6.25 * heightCm - 5 * age + (male ? 5 : -161);
        int target = (int) Math.round(bmr * activityFactor + goalAdjustment);
        return Math.max(1200, target);
    }

    public static int remaining(int target, int eaten, int burned) {
        return Math.max(0, target - eaten + burned);
    }
}
