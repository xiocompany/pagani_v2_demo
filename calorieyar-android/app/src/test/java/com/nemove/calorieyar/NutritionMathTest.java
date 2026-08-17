package com.nemove.calorieyar;

import org.junit.Test;
import static org.junit.Assert.*;

public class NutritionMathTest {
    @Test public void foodCalories_scalesAndRounds() {
        FoodItem rice = new FoodItem("rice", "برنج", "کفگیر", 210, 4.2, 45, 0.5);
        assertEquals(315, NutritionMath.foodCalories(rice, 1.5));
        assertEquals(0, NutritionMath.foodCalories(rice, -1));
    }

    @Test public void activityCalories_usesMetFormula() {
        assertEquals(226, NutritionMath.activityCalories(4.3, 75, 40));
        assertEquals(0, NutritionMath.activityCalories(0, 75, 40));
    }

    @Test public void remaining_addsBurnedCalories() {
        assertEquals(700, NutritionMath.remaining(2000, 1500, 200));
        assertEquals(0, NutritionMath.remaining(2000, 2500, 0));
    }

    @Test public void mifflin_hasSafeFloor() {
        assertTrue(NutritionMath.mifflinStJeor(30, 75, 175, true, 1.2, -500) >= 1200);
    }
}
