async def fetch_energy_data(modem_id, api_key, registrator_id, consumption_type, timezone):
    """Fetch energy data from the API based on the type of consumption."""
    
    # Get current time in Home Assistant's timezone
    local_tz = pytz.timezone(timezone)
    local_time = datetime.now(local_tz)

    start_of_year = local_time.replace(month=1, day=1, hour=0, minute=0, second=0)
    start_timestamp = int(start_of_year.timestamp())
    end_timestamp = int(local_time.timestamp())

    url = f"https://lk.curog.ru/api.data/get_values/?modem_id={modem_id}&key={api_key}&from={start_timestamp}&to={end_timestamp}"

    retries = 3
    for attempt in range(retries):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        break  # Exit loop if successful
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        logger.error(f"Failed to decode JSON, received: {text}")
                        return 0
                else:
                    text = await response.text()
                    logger.error(f"Error fetching data (attempt {attempt + 1}): {text}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)  # Wait before retrying
                    else:
                        return 0  # Return 0 after all attempts fail

    values = data["registrators"][registrator_id]["values"]
    current_date = local_time.strftime("%Y-%m-%d")
    current_month = local_time.strftime("%Y-%m")

    if consumption_type == "Daily Energy Consumption":
        filtered_data = [
            item for item in values 
            if datetime.utcfromtimestamp(item["timestamp"]).astimezone(local_tz).strftime("%Y-%m-%d") == current_date
        ]
    elif consumption_type == "Monthly Energy Consumption":
        filtered_data = [
            item for item in values 
            if datetime.utcfromtimestamp(item["timestamp"]).astimezone(local_tz).strftime("%Y-%m") == current_month
        ]
    else:
        return 0
    
    if len(filtered_data) > 1:
        return filtered_data[-1]["value"] - filtered_data[0]["value"]

    return 0


