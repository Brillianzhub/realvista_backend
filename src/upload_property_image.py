from django.core.files import File
from market.models import MarketProperty, PropertyImage 

def upload_property_image():
    # Retrieve the first MarketProperty object
    market_property = MarketProperty.objects.first()
    
    if not market_property:
        print("No MarketProperty objects found.")
        return

    print(f"Found MarketProperty: {market_property}")

    # File path to the image
    file_path = r"D:\DOCS\WEBRTC\projects\realvista_backend\src\property_images\goTo.png"
    
    try:
        # Open the file and create a PropertyImage instance
        with open(file_path, 'rb') as f:
            file_name = file_path.split("\\")[-1]  # Extract file name
            property_image = PropertyImage(
                property=market_property,
                image=File(f, name=file_name)
            )
            property_image.save()
        print("Image saved successfully!")
    except Exception as e:
        print(f"Error: {e}")
