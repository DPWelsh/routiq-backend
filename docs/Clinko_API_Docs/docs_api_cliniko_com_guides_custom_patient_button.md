Guides

/

Custom patient buttons

Last updated 3 months ago

## [link  to custom-patient-buttons](https://docs.api.cliniko.com/guides/custom_patient_button\#custom-patient-buttons) Custom patient buttons

Cliniko offers an additional integration option for applications that handlepatient data. This allows users to open these applications directly from Clinikoand potentially synchronize information on a given patient as needed.

### [link  to how-it-works-for-cliniko-users](https://docs.api.cliniko.com/guides/custom_patient_button\#how-it-works-for-cliniko-users) How it works for Cliniko users

Users can add these applications in a settings page underSettings > Our clinic > Integrations:

![Configuration panel](https://docs.api.cliniko.com/assets/custom-patient-buttons-config.0d765ec3e80c758c077426cb7090d497a70a3a7de6593350513e6b1eb923f88c.9bb1daa4.png)

This adds a new button to the Patient Actions bar for each patient:

![Patient actions with open dropdown](https://docs.api.cliniko.com/assets/patient-actions-open.7cb1d9c7bde70a9f60ec462f017a61f3ac5106c49853fbc976c7a66d2c99ee55.9bb1daa4.png)

Clicking on one of those buttons causes the user's browser to send a GET requestto the corresponding URL, with a query string of `patient_id=<Cliniko ID of displayed patient>`.If the user is logged into the other application, theyshould be taken directly to that application's information screen about thepatient with that Cliniko ID. If they're not logged in, they should beredirected to a login screen before they can see the patient information.

### [link  to how-it-works-for-integrators](https://docs.api.cliniko.com/guides/custom_patient_button\#how-it-works-for-integrators) How it works for integrators

If you want your application to integrate with Cliniko in this way, it shouldhave an endpoint prepared to receive GET requests from browsers with the querystring above. Requests made by unauthenticated users should be redirected to alogin screen. Once the user is authenticated, your application should displaythe information it has about the patient whose Cliniko ID was included in therequest. If you also integrate with Cliniko via its API, you can have yourapplication update its information on that patient via the API at this point.

Once your patient integration endpoint is ready, please get in contact with usso we can add its URL to our list of approved applications! Once that's done youshould be able to publish this URL to your users so they can add it to theconfig panel shown above and use the integration.

### [link  to registering-a-wildcard-url](https://docs.api.cliniko.com/guides/custom_patient_button\#registering-a-wildcard-url) Registering a wildcard URL

If you have multiple endpoints that you wish to receive requests on, you mayregister a URL with a wildcard first-level subdomain.

This wildcard subdomain will match any sequence of alphanumeric characters yourequire. Dashes `-` may be included but other special characters are not allowed.

For example, register the domain:

`*.example.com/patients`

And have your customer add:

`https://au.example.com/patients` or `https://staging-au1.example.com/patients`

Or any other subdomain.

Note that the wildcard is only valid one level deep. The following will fail:

`https://fr.eu.example.com/patients`

Previous page [Uploading patient attachments](https://docs.api.cliniko.com/guides/uploading_patient_attachments)

Next page [Time zone support](https://docs.api.cliniko.com/guides/time_zone_support)