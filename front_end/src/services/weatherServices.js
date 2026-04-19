const API_KEY = "52cbbbecad64e675e19e8c8f629e0b29";

export const getWeatherData = async(city)=>{

    try{
        const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric`);
        if(!response.ok){throw new Error('Network reponse was not ok');}
    
    return await response.json();}
    catch(error){console.error("Error fetching weather data:", error)};
    return null
    };

