package com.nemove.calorieyar;

public final class FoodItem {
    public final String id;
    public final String name;
    public final String unit;
    public final double calories;
    public final double protein;
    public final double carbs;
    public final double fat;

    public FoodItem(String id, String name, String unit, double calories, double protein, double carbs, double fat) {
        this.id = id;
        this.name = name;
        this.unit = unit;
        this.calories = calories;
        this.protein = protein;
        this.carbs = carbs;
        this.fat = fat;
    }
}
