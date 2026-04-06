import asyncio
import python_weather

async def main():
    async with python_weather.Client(unit=python_weather.METRIC) as client:
        w = await client.get('48.8566,2.3522')
        print(f"Current: T={w.temperature}, Hum={w.humidity}, Prec={w.precipitation}, Desc={w.description}")
        daily = list(w.daily_forecasts)[0]
        print("Daily attributes:", dir(daily))

asyncio.run(main())