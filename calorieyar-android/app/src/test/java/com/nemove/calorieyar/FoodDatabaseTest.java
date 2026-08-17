package com.nemove.calorieyar;

import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;

public class FoodDatabaseTest {
    @Test public void catalog_hasIranianFoods() {
        assertTrue(FoodDatabase.FOODS.size() >= 40);
        assertFalse(FoodDatabase.search("قورمه").isEmpty());
        assertFalse(FoodDatabase.search("برنج").isEmpty());
    }

    @Test public void emptySearch_returnsAllFoods() {
        List<FoodItem> result = FoodDatabase.search("   ");
        assertEquals(FoodDatabase.FOODS.size(), result.size());
    }
}
