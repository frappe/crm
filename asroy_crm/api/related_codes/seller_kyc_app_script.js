function onSubmit(e) {
  // Replace with your Frappe site URL and API endpoint. Use ngrok if testing locally.
  const frappeUrl = 'https://483e-27-147-130-214.ngrok-free.app/api/method/asroy_crm.api.seller_profile.create_seller_profile';

  // Replace with your API key and secret
  const headers = {
    'Authorization': 'token bce0d3b0e1ab189:81130845fccb8f9',
    'Content-Type': 'application/json'
  };

  // Extract form data from the event object
  const formData = e.namedValues;

  // Convert date to YYYY-MM-DD format
  const formatDate = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Prepare the payload
  const payload = {
    data: {
      salutation: formData['Salutation'] ? formData['Salutation'][0] : null,
      name1: formData['Name'] ? formData['Name'][0] : null,
      mobile: formData['Mobile'] ? formData['Mobile'][0] : null,
      mailing_address: formData['Mailing Address'] ? formData['Mailing Address'][0] : null,
      permanent_address: formData['Permanent Address'] ? formData['Permanent Address'][0] : null,
      email: formData['Email'] ? formData['Email'][0] : null,
      date_of_birth: formData['Date of Birth'] ? formatDate(formData['Date of Birth'][0]) : null,
      marital_status: formData['Marital Status'] ? formData['Marital Status'][0] : null,
      nationality: formData['Nationality'] ? formData['Nationality'][0] : null,
      nid_or_passport_number: formData['National Identification (NID)/Passport Number'] ? formData['National Identification (NID)/Passport Number'][0] : null,
      no_of_household_family_members: formData['Number of Family Members (Household)'] ? formData['Number of Family Members (Household)'][0] : null,
      number_of_adult_family_members: formData['Number of Family Members (Adults)'] ? formData['Number of Family Members (Adults)'][0] : null,
      number_of_children_family_members: formData['Number of Family Members (Children)'] ? formData['Number of Family Members (Children)'][0] : null,
      residency_status: formData['Residency Status'] ? formData['Residency Status'][0] : null,
      secondary_contact_person_name: formData['Secondary Contact Person Name'] ? formData['Secondary Contact Person Name'][0] : null,
      secondary_contact_person_mobile: formData['Secondary Contact Person Mobile'] ? formData['Secondary Contact Person Mobile'][0] : null,
      secondary_contact_person_relationship: formData['Secondary Contact Person Relationship'] ? formData['Secondary Contact Person Relationship'][0] : null,
      type_of_profession: formData['Type of Profession'] ? formData['Type of Profession'][0] : null,
      name_of_organization: formData['Name of Organization(s)'] ? formData['Name of Organization(s)'][0] : null,
      designation: formData['Designation(s)'] ? formData['Designation(s)'][0] : null,
      addresses_of_organization: formData['Addresses of Organization(s)'] ? formData['Addresses of Organization(s)'][0] : null,
      project_name: formData['Project Name'] ? formData['Project Name'][0] : null,
      project_address: formData['Project Address'] ? formData['Project Address'][0] : null,
      project_type: formData['Project Type'] ? formData['Project Type'][0] : null,
      location: formData['Location'] ? formData['Location'][0] : null,
      total_floors: formData['Total Floors'] ? formData['Total Floors'][0] : null,
      total_units: formData['Total Units'] ? formData['Total Units'][0] : null,
      land_size_katha: formData['Land Size (Katha)'] ? formData['Land Size (Katha)'][0] : null,
      road_size_feet: formData['Road Size (Feet)'] ? formData['Road Size (Feet)'][0] : null,
      developer_name: formData['Developer Name'] ? formData['Developer Name'][0] : null,
      handover_year: formData['Handover Year'] ? formData['Handover Year'][0] : null,
      building_type: formData['Building Type'] ? formData['Building Type'][0] : null,
      holding_type: formData['Holding Type'] ? formData['Holding Type'][0] : null,
      total_parkings: formData['Total Parkings'] ? formData['Total Parkings'][0] : null,
      finishing_status: formData['Finishing Status'] ? formData['Finishing Status'][0] : null,
      building_facing: formData['Building Facing'] ? formData['Building Facing'][0] : null,
      fair_facing: formData['Fair Facing'] ? formData['Fair Facing'][0] : null,
      gps_coordinate: formData['GPS Coordinate'] ? formData['GPS Coordinate'][0] : null,
      cctv: formData['CCTV'] ? formData['CCTV'][0] : null,
      security_guard: formData['Security Guard'] ? formData['Security Guard'][0] : null,
      fire_extinguisher: formData['Fire Extinguisher'] ? formData['Fire Extinguisher'][0] : null,
      fire_hydrant: formData['Fire Hydrant'] ? formData['Fire Hydrant'][0] : null,
      water_sprinkler: formData['Water Sprinkler'] ? formData['Water Sprinkler'][0] : null,
      reception_lobby: formData['Reception Lobby'] ? formData['Reception Lobby'][0] : null,
      electricity_backup: formData['Electricity Backup'] ? formData['Electricity Backup'][0] : null,
      cleaning_staff: formData['Cleaning Staff'] ? formData['Cleaning Staff'][0] : null,
      garbage_disposal: formData['Garbage Disposal'] ? formData['Garbage Disposal'][0] : null,
      prayer_room: formData['Prayer Room'] ? formData['Prayer Room'][0] : null,
      green_zone: formData['Green Zone'] ? formData['Green Zone'][0] : null,
      jogging_area: formData['Jogging Area'] ? formData['Jogging Area'][0] : null,
      gymnasium: formData['Gymnasium'] ? formData['Gymnasium'][0] : null,
      wheelchair_access: formData['Wheelchair Access'] ? formData['Wheelchair Access'][0] : null,
      game_or_sports_zone: formData['Game/Sports Zone'] ? formData['Game/Sports Zone'][0] : null,
      community_space: formData['Community Space'] ? formData['Community Space'][0] : null,
      floor_no: formData['Floor No'] ? formData['Floor No'][0] : null,
      unit_no: formData['Unit No'] ? formData['Unit No'][0] : null,
      occupancy_status: formData['Occupancy Status'] ? formData['Occupancy Status'][0] : null,
      gross_area_square_feet: formData['Gross Area (Square Feet)'] ? formData['Gross Area (Square Feet)'][0] : null,
      gross_area_specific: formData['Gross Area Specific'] ? formData['Gross Area Specific'][0] : null,
      no_of_parking: formData['No of Parking'] ? formData['No of Parking'][0] : null,
      net_area_square_feet: formData['Net Area (Square Feet)'] ? formData['Net Area (Square Feet)'][0] : null,
      property_facing: formData['Property Facing'] ? formData['Property Facing'][0] : null,
      no_of_beds: formData['No of Beds'] ? formData['No of Beds'][0] : null,
      no_of_baths: formData['No of Baths'] ? formData['No of Baths'][0] : null,
      no_of_livings: formData['No of Livings'] ? formData['No of Livings'][0] : null,
      no_of_balconies: formData['No of Balconies'] ? formData['No of Balconies'][0] : null,
      maid_quarters: formData['Maid Quarters'] ? formData['Maid Quarters'][0] : null,
      store_room: formData['Store Room'] ? formData['Store Room'][0] : null,
      flooring: formData['Flooring'] ? formData['Flooring'][0] : null,
      floor_titles_size: formData['Floor Titles Size'] ? formData['Floor Titles Size'][0] : null,
      fittings_brand: formData['Fittings Brand'] ? formData['Fittings Brand'][0] : null,
      asking_price_bdt: formData['Asking Price (BDT)'] ? formData['Asking Price (BDT)'][0] : null,
      bottom_price_bdt: formData['Bottom Price (BDT)'] ? formData['Bottom Price (BDT)'][0] : null,
      pricing_specific: formData['Pricing Specific'] ? formData['Pricing Specific'][0] : null,
      bastuana_service_charge_bdt: formData['Bastuana Service Charge (BDT)'] ? formData['Bastuana Service Charge (BDT)'][0] : null,
      bastuana_service_charge_specific: formData['Bastuana Service Charge Specific'] ? formData['Bastuana Service Charge Specific'][0] : null,
      property_monthly_rent_bdt: formData['Property Monthly Rent (BDT)'] ? formData['Property Monthly Rent (BDT)'][0] : null,
      property_monthly_service_charge_bdt: formData['Property Monthly Service Charge (BDT)'] ? formData['Property Monthly Service Charge (BDT)'][0] : null,
      viewing_contact_name: formData['Viewing Contact Name'] ? formData['Viewing Contact Name'][0] : null,
      viewing_contact_mobile: formData['Viewing Contact Mobile'] ? formData['Viewing Contact Mobile'][0] : null,
      viewing_access: formData['Viewing Access (Time, Day, etc.)'] ? formData['Viewing Access (Time, Day, etc.)'][0] : null,
      no_of_owners_of_the_property: formData['No of Owners of the Property'] ? formData['No of Owners of the Property'][0] : null,
      registration_status: formData['Registration Status'] ? formData['Registration Status'][0] : null,
      mutation: formData['Mutation'] ? formData['Mutation'][0] : null,
      holding_tax: formData['Holding Tax'] ? formData['Holding Tax'][0] : null,
      mortgage_against_property: formData['Mortgage Against Property'] ? formData['Mortgage Against Property'][0] : null,
      mortgage_details: formData['Mortgage Details (Institution, Amount, etc.)'] ? formData['Mortgage Details (Institution, Amount, etc.)'][0] : null
    }
  };

  // Log the payload for debugging
  Logger.log(JSON.stringify(payload));

  // Send data to Frappe
  const options = {
    method: 'post',
    headers: headers,
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(frappeUrl, options);
  Logger.log(response.getContentText()); // Log the response for debugging
}

// Install the trigger to run the function on form submission
function installTrigger() {
  ScriptApp.newTrigger('onSubmit')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onFormSubmit()
    .create();
}