# QA Report — CalorieYar Android V1

## Automated verification
- NutritionMath unit tests
- Food catalog/search unit tests
- Android Lint
- Debug APK assembly
- APK artifact existence/non-empty check

## Functional scope reviewed
- App launch flow
- RTL layout
- Food search and log
- Activity log and MET calculation
- Daily totals and macros
- History delete
- Settings persistence
- Android 13+ notification permission request
- Alarm scheduling and boot restore logic

## Known V1 boundaries
- Database is intentionally local-only.
- MCP/OpenAI is not connected in V1; UI and core are prepared for it as the next product layer.
- Calorie values are approximate reference values and can be expanded/replaced with a validated nutrition database later.
