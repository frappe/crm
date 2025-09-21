function onSubmit(e) {
  // Replace with your Frappe site URL and API endpoint. Used ngrok.
  const frappeUrl = 'https://1092-27-147-130-214.ngrok-free.app/api/method/asroy_crm.api.buyer_profile.create_buyer_profile';

    // Replace with your API key and secret (if required)
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
  
    const payload = {
      data: {
        salutation: formData['Salutation'] ? formData['Salutation'][0] : null,
        name1: formData['Name'] ? formData['Name'][0] : null,
        email: formData['Email'] ? formData['Email'][0] : null,
        mobile: formData['Mobile'] ? formData['Mobile'][0] : null,
        date_of_birth: formData['Date of Birth'] ? formatDate(formData['Date of Birth'][0]) : null,
        designation: formData['Designation(s)'] ? formData['Designation(s)'][0] : null,
        nationality: formData['Nationality'] ? formData['Nationality'][0] : null,
        nid_no: formData['National Identification (NID)/Passport Number'] ? formData['National Identification (NID)/Passport Number'][0] : null,
        mailing_address: formData['Mailing Address'] ? formData['Mailing Address'][0] : null,
        permanent_address: formData['Permanent Address'] ? formData['Permanent Address'][0] : null,
        type_of_profession: formData['Type of Profession'] ? formData['Type of Profession'][0] : null,
        marital_status: formData['Marital Status'] ? formData['Marital Status'][0] : null,
        relation_with_secondary_contact_person: formData['Relation with Secondary Contact Person'] ? formData['Relation with Secondary Contact Person'][0] : null,
        secondary_contact_person_mobile: formData['Secondary Contact Person Mobile'] ? formData['Secondary Contact Person Mobile'][0] : null,
        secondary_contact_person_name: formData['Secondary Contact Person Name'] ? formData['Secondary Contact Person Name'][0] : null,
        residency_status: formData['Residency Status'] ? formData['Residency Status'][0] : null,
        no_of_children_family_members: formData['Number of Family Members (Children)'] ? formData['Number of Family Members (Children)'][0] : null,
        no_of_adult_family_members: formData['Number of Family Members (Adults)'] ? formData['Number of Family Members (Adults)'][0] : null,
        no_of_household_family_members: formData['Number of Family Members (Household)'] ? formData['Number of Family Members (Household)'][0] : null,
        name_of_organization: formData['Name of Organization(s)'] ? formData['Name of Organization(s)'][0] : null,
        address_of_organization: formData['Address of Organization(s)'] ? formData['Address of Organization(s)'][0] : null,
        location: formData['Locations'] ? formData['Locations'][0] : null,
        location_comments: formData['Location Comments'] ? formData['Location Comments'][0] : null,
        property_type: formData['Property Type'] ? formData['Property Type'][0] : null,
        property_size_squar_feet: formData['Property Size (Squar Feet)'] ? formData['Property Size (Squar Feet)'][0] : null,
        property_condition: formData['Property Condition'] ? formData['Property Condition'][0] : null,
        property_size_katha: formData['Property Size (Katha)'] ? formData['Property Size (Katha)'][0] : null,
        no_of_beds: formData['No of Beds'] ? formData['No of Beds'][0] : null,
        no_of_baths: formData['No of Baths'] ? formData['No of Baths'][0] : null,
        no_of_balconies: formData['No of Balconies'] ? formData['No of Balconies'][0] : null,
        no_of_car_parking: formData['No of Car Parking'] ? formData['No of Car Parking'][0] : null,
        budget_bdt: formData['Budget (BDT)'] ? formData['Budget (BDT)'][0] : null,
        financial_mode: formData['Financial Mode'] ? formData['Financial Mode'][0] : null
      }
    };
  
    // Log the payload for debugging
    Logger.log(JSON.stringify(payload));
  
    // Send data to Frappe
    const options = {
      method: 'post',
      headers: headers,
      payload: JSON.stringify(payload),
      muteHttpExceptions: true // Add this to capture full response
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