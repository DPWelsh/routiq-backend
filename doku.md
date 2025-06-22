Logodoku
Search
Introduction
Channels and Features
Getting Started
DOKU Hosted API
Payment Request
Identify
Redirect
Notify
Merchant Hosted API
Other API & Callback
Response Code
Payment Channel Code
Test Data & Simulator
Going Live
Version
Powered by DOKU
Introduction
The DOKU API supports two methods of payment processing – namely, merchant-hosted and DOKU-hosted. See below for features of each service:

DOKU Hosted (DH) Instant payment services where the payment input form is located within the DOKU page. The selection of payment methods can be done on the merchant or DOKU page. With this service, the customer will be redirected to a DOKU-hosted page upon checkout to complete the payment.

Merchant Hosted (MH) The payment page and data input is native to the merchant’s website, without having to redirect to a DOKU-hosted page. Having the payment form on the merchant page does not compromise the security of the cardholder however, none of the cardholder data will actually be stored on the merchant’s server.

Channels and Features
Credit card
DOKU accept all credit card issued with these Principals:

Mastercard
Visa
JCB (Only for BNI Acquiring)
Credit card transaction in Indonesia Online Merchant is usually required additional security from issuer Bank, called 3D Secure (3DS). This process will ask the genuine credit card holder to enter Internet PIN or One Time PIN (OTP) that usually sent to Credit Card Holder mobile phone.

BIN Filtering
Each card issuer has a unique BIN (Bank Identification Number), which is made up of the first 6 digits in the Credit Card number. The conditions set in the filter will specify which BIN numbers that are allowed to make payments on your site. When a card number that has been blocked by the BIN filter is entered, the DOKU server will not be able to process the payment.

Installment
DOKU supported credit card installment payment. There are 2 types of installment type supported:

On-us installment, where card issuer and card acquirer are from the same bank.
Off-us installment, where card issuer and card acquirer are from different bank. Transaction conversion from regular to installment will be processed manually from each Card issuer.
Merchant can trigger installment payment by adding some parameters in payment request to DOKU.

Tokenization
Tokenization enables the customer to make a purchase without having to input card details or personal information, apart from the CVV number. This process is typically used by merchants that have repeat customers who will benefit from a faster checkout by reducing the number of fields the customer needs to fill in. If the card issuer requires 3D secure verification process, the customer will still have to complete this to make a purchase. In order for this process to work, the customer enters all of the card information only during the very first time they make a purchase. DOKU stores this data in a secure form and gives the merchant a token, which is paired to the customer’s login credentials on the merchant website. After this process has been completed, each time they make a payment from hereon out, they only have to input the CVV.

Recurring
Recurring payment takes it a step further and allows the customer to make a purchase with a single click on the website. This means that they can skip the process of inputting their card details, personal information, CVV number and 3D secure. The customer will have to enter the card details and complete the 3D secure verification process only during the first time they make a purchase. By eliminating the extra steps, you are able to create a more seamless and easy checkout process, which may lead to a lower drop-off rate. However, please note that this is subject to DOKU’s and the bank’s approval due to an increase in fraud risk.

Authorize and Capture
Authorize & Capture is a feature that allows you to block a certain amount from the customer’s credit card limit (Authorize), then hold it for a certain period before charging a payment – which can be a different amount from what you block (Capture).

DOKU Wallet
DOKU Wallet is an electronic money service issued by DOKU. DOKU has grant license to issue e-money from Bank Indonesia. For more information about DOKU Wallet, you can check on the website

Internet Banking
DOKU accept bank account debit payment and consumer financing payment. All of it is categorized as internet banking payment. Below are the list of internet banking channels and the supported API:

Payment Channel	API supported
Mandiri Clickpay	DH & MH
BCA Klikpay	DH
BRI e-Pay	DH
Muamalat	DH
Danamon	DH
Permata Net	DH
CIMBClicks	DH
Kredivo	DH
KlikBCA	KlikBCA API
BNI Yap!	BNI Yap API
DH = DOKU Hosted, MH = Merchant Hosted
Virtual Account
Virtual Account Number is issued for banks or convenience stores payment. Payment is initiated from bank's or convenience store's channels such as ATM, mobile banking, internet banking, or over the counter / teller.

Payment Channel	API	Off-us
Permata	DH & MH	Yes
BCA	DH & MH	No
Mandiri	DH & MH	Yes
Sinarmas	DH & MH	Yes
CIMB Niaga	DH & MH	Yes
Danamon	DH & MH	Yes
BRI	DH & MH	Yes
BNI VA	DH	Yes
Alfa	DH & MH	No
Indomaret	DH & MH	No
QNB	MH	Yes
BTN	MH	Yes
Maybank	DH & MH	Yes
Arta Jasa	DH & MH	Yes
DH = DOKU Hosted, MH = Merchant Hosted, Off-us = payment from other acquirer channel
Direct inquiry
Direct inquiry is a feature that allows DOKU to inquire Virtual Account Number / Payment Code to merchant when payment inquiry is requested from bank or convenience store. To integrate direct inquiry, merchant should respond payment inquiry as defined in this specification.

Reusable
Reusable is a feature that allows merchant's customer to pay a Virtual Account multiple times without the same Virtual Account Number / Payment Code getting expired.

Check Status, Void, Refund, Cancellation
Check Status Feature
DOKU provide feature for merchant to check status of the payment transaction. To implement Check Status, please find API here

Void, Refund, Cancellation
There are some methods to modify status of success transaction:

Void is cancelling unsettled credit card transaction. Please find API here
Refund is cancelling settled credit card transaction. Please find API here
Cancellation is an API to Void or Refund success transaction in a single request. If transaction is unsettled, DOKU will request Void to bank. If transaction is settled, DOKU will send Refund request to bank. Please find API here
Getting Started
To integrate, merchant should have ID from DOKU which is called Mall ID or Merchant Code. Please register on DOKU Merchant to get your ID.
Prepare some URL and page in testing and production environment, especially for DOKU Hosted integration.
Special Characters
Due to security purpose, not all special characters are allowed in parameters sent. Special characters allowed by DOKU are:

, . & ; + : / =

Currency and Country code
DOKU use ISO3166 as country and currency code standard. You can see the code list on this URL:

https://www.iso.org/obp/ui/

DOKU IP Address / URL
Sample of IP filtering

DOKU has only 3 IP public that can be detected when DOKU call to your application (Identify, Notify & Redirect functions). So to make those applications process ONLY from DOKU is by using DOKU IP Address. Although, High Anonymous Proxy or IP Masking/Hide/Change tools on most current network application can still penetrate this feature, this will reduce most of injection false information to the applications to create genuine transactions.

Below are the URL of DOKU API:

Staging URL https://staging.doku.com/

Production URL https://pay.doku.com/

Shared Key Hash Value
To secure the communication, besides IP filtering, DOKU implements Shared Key Hash Value - an additional parameter from Merchant or DOKU, called WORDS. This parameter value is hashed using 4 options hash method with combination of Shared Key. The hashed WORDS generated by Merchant will be validated with hashed WORDS generated by DOKU System and vice versa. If match, then it will be considered genuine request or response. Four options hash methods that Merchant can choose are: SHA1, SHA256, HMAC-SHA1, HMAC-SHA256.

Sample using IDR:

$WORDS=sha1(40000.00123map_aztec977872);
Sample using USD Currency:

$WORDS=sha1(40000.00123map_aztec977872);
Below is a sample combination string:

WORDS = sha1 (AMOUNT + MALLID + Shared Key + TRANSIDMERCHANT )

Or if using currency other than IDR :

WORDS = sha1 (AMOUNT + MALLID + Shared Key + TRANSIDMERCHANT + CURRENCY)

Shared Key is generated by DOKU and displayed in Settings menu on DOKU Merchant dashboard.

All these parameters are being combined without any spaces. The position of the parameters are in FIXED order. You SHOULD NOT swap the order.
The Shared Key MUST NOT BE REVEALED to public. As it is your merchant’s secure credential. And this Shared Key may/may not be changed accordingly.
DOKU Hosted API
DOKU Hosted flow

Before integration, it is recommended to configure some URL in DOKU Merchant dashboard. You can check the configuration in menu 'Settings > API Setting'. URL that can be configured are:

URL Identify
URL Notify
URL Redirect
URL Review
Payment Request
Endpoint	Method	Definition
/Suite/Receive	HTTP POST	Merchant submits payment request using HTML Post from Customer's browser to DOKU Hosted Payment Page
Parameters for Payment Request
 Please note that parameters in bold red font is mandatory, and parameters in normal font is optional. If optional parameter sent in invalid format or length, DOKU will set value to NULL.
 Definition in "Type" column: A=Alphabet, AN=Alphanumeric, ANS=Alphanumeric & Special Characters
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. If not using Chain, use value: NA
AMOUNT	N	12.2	Total amount. Eg: 10000.00
PURCHASEAMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
PAYMENTTYPE	AN	13	SALE or AUTHORIZATION. Default is SALE
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT For transaction with currency other than 360 (IDR), use:
AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+CURRENCY
For Shared Key, refer to Shared Key Hashed Value
REQUESTDATETIME	N	14	YYYYMMDDHHMMSS
CURRENCY	N	3	ISO3166, numeric code
PURCHASECURRENCY	N	3	ISO3166, numeric code
SESSIONID	AN	48	Merchant can use this parameter for additional validation, DOKU will return the value in other response process.
NAME	AN	128	Customer / Buyer name
EMAIL	ANS	254	Customer / Buyer email
ADDITIONALDATA	ANS	1024	Custom additional data for specific merchant use
BASKET	ANS	1024	Show transaction description. Use comma to separate each field and semicolon for each item. E.g. Item1,1000.00,2,20000.00;item2,15000.00,2,30000.00
SHIPPING_ADDRESS	ANS	100	Mandatory for Kredivo payment channel. Shipping address contains street and number
SHIPPING_CITY	ANS	100	Mandatory for Kredivo payment channel. City name
SHIPPING_STATE	AN	100	State or Province name
SHIPPING_COUNTRY	ANS	3	Mandatory for Kredivo payment channel. ISO3166, alpha
SHIPPING_ZIPCODE	ANS	10	Mandatory for Kredivo payment channel. ZIP Code
PAYMENTCHANNEL	N	2	See Payment Channel Code
ADDRESS	ANS	100	Home address contains street and number
CITY	ANS	100	City name
STATE	AN	100	State or Province name
COUNTRY	A	3	ISO3166, alpha
ZIPCODE	N	10	Zip Code
HOMEPHONE	ANS	11	Home Phone
MOBILEPHONE	ANS	15	Mobile Phone
WORKPHONE	ANS	13	Work Phone / Office Phone
BIRTHDATE	N	8	YYYYMMDD
 Please note that in "BASKET" parameter, DOKU separate value by comma and semicolon. Make sure that you don't send value with comma or semicolon if it's not meant to be separated.
Additional Parameters for Airlines
Airlines merchant is required to send some additional specific parameters on payment request. Below are the parameters:

Parameter	Type	Length	Description
FLIGHT	N	2	01 for Domestic, 02 for International
FLIGHTTYPE	N	1	0 : One Way, 1 : Return, 2 : Transit, 3 : Transit & Return, 4 : Multiple Cities
BOOKINGCODE	AN	20	Booking code generated by Airline
ROUTE*	AN	50	List of route using format XXX-YYY (from XXX to YYY). E.g. : CGK-DPS
FLIGHTDATE*	AN	8	List of flight date using format YYYYMMDD
FLIGHTTIME*	AN	6	List of flight time using format HHMMSS
FLIGHTNUMBER*	AN	30	List of flight number using IATA Standard. XXYYYY (XX = Airline Name, YYYY = Flight Number)
PASSENGER_NAME*	ANS	50	List of passenger name in one booking code
PASSENGER_TYPE*	AN	1	List of passenger type in one booking. A : Adult, C : Child
VAT	N	12.2	Total VAT. Eg: 10000.00
INSURANCE	AN	12.2	Total Insurance. Eg: 10000.00
FUELSURCHARGE	AN	12.2	Total fuel surcharge. Eg: 10000.00
THIRDPARTY_STATUS	ANS	1	0 : Travel Arranger joins the flight, 1 : Travel Arranger does not join the flight
FFNUMBER	ANS	16	Frequent Flyer Number. If no Frequent Flyer Number, send "0"
 * : For parameter with multiple value (list), please send same parameter name with different value. e.g.: PASSENGER_NAME=John&PASSENGER_NAME=Erica
Additional Parameters for Credit Card Installment
Credit Card Installment payment require some additional specific parameters on payment request. Below are the parameters:

Parameter	Type	Length	Description
INSTALLMENT_ACQUIRER	N	3	Acquirer code for installment
TENOR	N	2	Number of month to pay the installment
PROMOID	N	3	Promotion ID from the bank for the current merchant
Additional Parameters for Tokenization (First Payment)
In the DOKU Hosted API, Credit Card Tokenization is treated as a separate payment method from the un-tokenized Credit Card. Please send PAYMENTCHANNEL parameter in Payment Request with value 16.

Parameter	Type	Length	Description
CUSTOMERID	AN	16	Merchant’s customer identifier
PAYMENTCHANNEL	N	2	16
Additional Parameters for Second Payment Request
Parameter	Type	Length	Description
CUSTOMERID	AN	16	Merchant’s customer identifier
TOKENID	AN	16	Tokenized Card Identifier
PAYMENTCHANNEL	N	2	16
If merchant sent Payment Channel `16` but did not send CUSTOMERID, DOKU will use EMAIL value as CUSTOMERID value.
Additional Parameters for Recurring Registration
In the DOKU-Hosted API, Credit Card Recurring is treated as a separate payment method. Please send PAYMENTCHANNEL parameter in Payment Request with value 17.

Parameter	Type	Length	Description
CUSTOMERID	AN	16	Merchant’s customer identifier
BILLNUMBER	AN	16	Merchant’s bill identifier
BILLDETAIL	ANS	256	Product information
BILLTYPE	A	1	S= Shopping, I = Installment, D = Donation, P = Payment
STARTDATE	N	8	Recurring start date yyyyMMdd
ENDDATE	N	8	Recurring end date yyyyMMdd , NA = end date not specified
EXECUTETYPE	A	4	DAY or DATE or FULLDATE
EXECUTEDATE	AN	3	If EXECUTETYPE = DAY then SUN / MON / TUE / WED / THU / FRI / SAT . If EXECUTETYPE = DATE then 1/2/3/.../28 . If EXECUTETYPE = FULLDATE then list of execute dates in yyyyMMdd
EXECUTEMONTH	A	3	JAN / FEB / MAR / APR / MAY / JUN / JUL / AUG / SEP / OCT / NOV / DEC
FLATSTATUS	A	5	If the amount is dynamic, use value: FALSE. Use TRUE if the amount is fixed.
REGISTERAMOUNT	N	12.2	Registration amount Eg: 10000.00
Identify
Allow Merchant to identify the payment channel that Customer has chosen. Merchant should configure Identify URL in DOKU Merchant Dashboard settings. Example : http://www.yourwebsite.com/directory/DOKU_identify.php

This IDENTIFY Process is not a mandatory process. This IDENTIFY process also does not require Merchant’s response. Feel free to use or not use this process based on your business process and requirement.

Parameters for Identify
Parameter	Type	Length	Description
AMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
PAYMENTCHANNEL	N	2	See Payment Channel Code
SESSIONID	AN	48	DOKU will return the value from Payment Request
Redirect
Redirecting back to Merchant’s domain. Merchant should inform the URL where DOKU will redirect. Example: http://www.yourwebsite.com/directory/DOKU_redirect.php

Parameters for Redirect
Parameter	Type	Length	Description
AMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order: AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS
For transaction with currency other than 360 (IDR), use : AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS+CURRENCY
Refer to Shared Key Hashed Value
STATUSCODE	N	4	0000: Success, others Failed
PAYMENTCHANNEL	N	2	See Payment Channel Code
SESSIONID	AN	48	DOKU will return the value from Payment Request
PAYMENTCODE	N	16	Virtual Account identifier for VA transaction. Has value if using Channel that has payment code.
CURRENCY	N	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
Notify
Notify API allows Merchant to have a real-time payment status notification. Merchant should inform the URL where DOKU server will send the notification message. Example: http://www.yourwebsite.com/directory/DOKU_notify.php

By default DOKU will IGNORE merchant’s response but merchant have an option for DOKU to reverse the payment if merchant’s response is not appropriate or time out occurs.

Respond Notify

print CONTINUE
Parameters for Notify
Parameter	Type	Length	Description
AMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order: AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS
For transaction with currency other than 360 (IDR), use : AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS+CURRENCY
Refer to Shared Key Hashed Value
STATUSTYPE	A	1	Default value : P
RESPONSECODE*	N	4	0000: Success, others Failed
APPROVALCODE	AN	20	Transaction number from bank
RESULTMSG*	A	20	SUCCESS or FAILED
PAYMENTCHANNEL	N	2	See Payment Channel Code
PAYMENTCODE	N	8	Virtual Account identifier for VA transaction. Has value if using Channel that has payment code.
SESSIONID	AN	48	DOKU will return the value from Payment Request.
BANK	AN	100	Bank Issuer
MCN	ANS	16	Masked card number
PAYMENTDATEANDTIME	N	14	YYYYMMDDHHMMSS
VERIFYID	N	30	Generated by Fraud Screening (RequestID)
VERIFYSCORE	N	3	-1 or 0 - 100
VERIFYSTATUS	A	10	APPROVE / REJECT / REVIEW / HIGHRISK / NA
CURRENCY	N	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
BRAND	A	10	VISA / MASTERCARD
CHNAME	AN	50	Cardholder Name
THREEDSECURESTATUS	A	5	TRUE or FALSE
LIABILITY	A	10	CUSTOMER / MERCHANT / NA
EDUSTATUS	A	10	Manual Fraud Review, value : APPROVE / REJECT / NA (default)
CUSTOMERID	AN	16	Merchant’s customer identifier (If using Tokenization)
TOKENID	AN	16	Merchant’s customer identifier (If using Tokenization)
* Main identifier of transaction success / failed

Merchant Hosted API
Merchant hosted integration is more advanced than DOKU Hosted. DOKU provide sample function to facilitate Merchant to integrate with Merchant Hosted API. Below are the list of sample functions:

DOKU sample function to create WORDS in PHP. Please find sample code here
DOKU sample function to request to DOKU API in PHP. Please find sample code here
DOKU sample function to save API URL. Please find sample code here
Credit Card Integration
Step 1

<script src="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.pack.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css" rel="stylesheet">
<script src="http://staging.doku.com/doku-js/assets/js/doku-1.2.js"></script>
<link href="http://staging.doku.com/doku-js/assets/css/doku.css" rel="stylesheet">
To get started on your integration, follow these steps one by one by pasting the template scripts onto your website. The DOKU payment form is saved in HTML format; the template script acts as a placeholder for where the payment form will appear on your page. Prepare your HTML pages as seen in the template, and customize accordingly.

Step 1: Insert the doku-1.2.js, fancybox.js and fancybox.css onto your website’s payment page, along with your custom style.

Step 2

<?php require_once('../Doku.php');
Doku_Initiate::$sharedKey = ‘<Put Your Shared Key Here>’;
Doku_Initiate::$mallId = ‘<Put Your Merchant Code Here>’;
$invoice = 'invoice_1458123951’;
$params = array('amount' => '10000.00','invoice' => $invoice, 'currency' => '360');
$words = doku_Library::doCreateWords($params); ?>
Step 2: Initialize the payment form by creating the 'WORDS' using function sample

Step 3

<script type="text/javascript">
$(function() {
var data = new Object();
data.req_merchant_code = '1';
data.req_chain_merchant = 'NA';
data.req_payment_channel = '15'; // ‘15’ = credit card
data.req_transaction_id = '<?php echo $invoice ?>';
data.req_currency = '<?php echo $currency ?>';
data.req_amount = '<?php echo $amount ?>';
data.req_words = '<?php echo $words ?>';
data.req_form_type = 'full';
getForm(data, ‘staging’); //for production environment, change ‘staging’ to ‘production’
});
</script>
Step 3: Add following example script on to webpage

Step 4

<form action="charge.php" method="POST" id="payment-form">
    <div doku-div='form-payment'>
        <input id="doku-token" name="doku-token" type="hidden" />
        <input id=" doku-pairing-code" name="doku-pairing-code" type="hidden" />
    </div>
</form>
Step 4: Insert the template script where you wish the payment form to appear on your website.
When completed correctly, the payment form should appear as seen below, and you may start receiving payments immediately. The DOKU script only provides the four fields to be filled in by the customer. All other parts of the payment page, including the logo and ‘Process Payment’ button are customizable to your needs for a completely white label payment flow.

Credit Card Payment form

Once your customer has input their card data and clicked the “Process Payment” button, the data will be processed by DOKU. The DOKU server then responds with the card ID, and the browser will post the data to the merchant server, according to the URL set in your action form.

Payment Request Sample

<?php require_once('../Doku.php');
Doku_Initiate::$sharedKey = ‘<Put Your Shared Key Here>’;
Doku_Initiate::$mallId = ‘<Put Your Merchant Code Here>’;
$token = $_POST['doku-token'];
$pairing_code = $_POST['doku-pairing-code'];
$invoice_no = $_POST['doku-invoice-no'];
$params = array('amount' => '10000.00', 'invoice' => $invoice_no, 'currency' => '360', 'pairing_code' => $pairing_code, 'token' => $token);
$words = Doku_Library::doCreateWords($params);
$basket[] = array('name' => 'sayur', 'amount' => '10000.00', 'quantity' => '1', 'subtotal' => '10000.00');
$customer = array('name' => 'TEST NAME','data_phone' => '08121111111', 'data_email' => 'test@test.com', 'data_address' => 'bojong gede #1 08/01');
$dataPayment = array('req_mall_id' => Doku_Initiate::$mallId, 'req_chain_merchant' => 'NA','req_amount' => '10000.00','req_words' => $words, 'req_purchase_amount' => '10000.00', 'req_trans_id_merchant' => $invoice_no, 'req_request_date_time' => date('YmdHis'), 'req_currency' => '360', 'req_purchase_currency' => '360', 'req_session_id' => sha1(date('YmdHis')), 'req_name' => $customer['name'], 'req_payment_channel' => 15, 'req_basket' => $basket, 'req_email' => $customer['data_email'], 'req_token_id' => $token);
$result = Doku_Api::doPayment($dataPayment);
if($result->res_response_code == '0000'){
    echo 'SUCCESS';   //success
}else{
    echo 'FAILED';  //failed }
Due to potential fraud, Indonesia is a 3D Secure market, where customer authentication is required to proceed with the transaction. The form of authentication differs form each bank, but typically it involves a One-Time Password sent via SMS. Not all issuing banks in Indonesia have implemented 3D secure, but the majority of them have. Further assessment by DOKU and the acquiring bank is required to grant a non-3D secure Merchant ID.

You can retrieve the posted data from the form within your server. Then send the payment request to the DOKU server to be processed using our sample function.

BIN Filtering integration
BIN filtering

In order to apply the BIN filter, you must insert the following conditions into a prepayment request. The prepayment request must be sent before the actual payment request. You can add several conditions by separating with a comma. Afterwards, you may insert your original payment request form.

Tokenization integration
Follow these steps to apply tokenization to your credit card payment process:

Tokenization Step 1

<script type="text/javascript">
$(function() {
var data = new Object();
data.req_merchant_code = '1';
data.req_chain_merchant = 'NA';
data.req_payment_channel = '15';
data.req_transaction_id = '<?php echo $invoice ?>';
data.req_currency = '<?php echo $currency ?>';
data.req_amount = '<?php echo $amount ?>';
data.req_words = '<?php echo $words ?>';
data.req_form_type = 'full';
data.req_customer_id = '12124';
getForm(data, ‘staging’); //for production environment, change ‘staging’ to ‘production’
});
</script>
Step 1: Insert the additional script to your server under the payment data.

To initialize tokenization, follow the same steps as general credit card processing, but add the additional parameter “data.reg_customer_id” to your javascript under the payment data. The “data.reg_customer_id” parameter may represent the customer ID that you assign to each customer within your database. This ID will be paired with the token that DOKU gives in the status response.

The javascript with the additional parameter will generate the following payment form, which enables the customer to save their credit card, for faster payment. When a transaction is sent as a tokenization to DOKU, in addition to the 4 fields for credit card data, DOKU will also display on the merchant website a tick box asking the customer’s approval to save the card.

Credit Card Tokenization Payment form

Tokenization Step 2

{
"res_approval_code":"844647",
"res_trans_id_merchant":"1706221359",
"res_amount":"30000.00",
"res_payment_date_time":"20160319114638",
"res_verify_score":"-1",
"res_verify_id":"",
"res_verify_status":"NA",
"res_words":"7553a51a091775a2462eb9150c7135f4a8d58ff161db022ca42e0ef65666ebf0",
"res_response_msg":"SUCCESS",
"res_mcn":"4***********1111",
"res_mid":"000100013000195",
"res_bank":"JPMORGAN CHASE BANK",
"res_response_code":"0000",
"res_session_id":"4cf212f141a1d7fe672db93db75cc069,PRODUCTION",
"res_payment_channel":"15",
"res_bundle_token":"{"res_token_payment":"0bea1c1c653dbc8e1e6c24155c629fe237325a06", "res_token_msg":"SUCCESS", "res_token_code":"0000" }"
}
Step 2: Generate and save the token during the first payment.

When the customer has filled in their card details and clicked “Process Payment”, the data is sent to the DOKU server. Because the ‘data.reg_customer_id’ parameter has been added to the payment form, the DOKU server will create a token to pair with the Customer ID. If the customer checks the box next to “Save this Credit Card for faster checkout?” the payment response to the Merchant server will include this token.

Tokenization Step 3

<script type="text/javascript">
$(function() {
var data = new Object();
data.req_merchant_code = '1';
data.req_chain_merchant = 'NA';
data.req_payment_channel = '15';
data.req_transaction_id = '<?php echo $invoice ?>';
data.req_currency = '<?php echo $currency ?>';
data.req_amount = '<?php echo $amount ?>';
data.req_words = '<?php echo $words ?>';
data.req_form_type = 'full';
data.req_customer_id = '12124';
data.req_token_payment = '0bea1c1c653dbc8e1e6c24155c629fe237325a06';
getForm(data, ‘staging’);  //for production environment, change ‘staging’ to ‘production’
});
</script>
Step 3: For subsequent payments, retrieve the token from your database and send it to the DOKU server.

After a successful first payment, (assuming that the merchant has been correctly storing the Token data) only a slight modification needs to be made to the javascript. Add the extra parameter ‘data.reg_token_payment’ as seen below, by using the token value that was obtained during the first payment.

The sample script will generate following payment form:

Credit Card Tokenization filled Payment form

As you can see from the image above, the customer no longer needs to fill out the credit card data apart from the CVV number. When the customer clicks the “Process Payment” button, it will follow the same process as regular card payments.

Register Recurring integration
Follow these steps to apply Register recurring payment to your credit card payment process:

<script type="text/javascript">
$(function() {
var data = new Object();
data.req_merchant_code = '1';
data.req_chain_merchant = 'NA';
data.req_payment_channel = '15';
data.req_transaction_id = '<?php echo $invoice ?>';
data.req_currency = '<?php echo $currency ?>';
data.req_amount = '<?php echo $amount ?>';
data.req_words = '<?php echo $words ?>';
data.req_form_type = 'full';
data.req_customer_id = '12124';
getForm(data, ‘staging’); //for production environment, change ‘staging’ to ‘production’
});
</script>
Step 1: Insert the additional script to your server under the payment data. To initialize recurring payment, follow the same steps as general credit card processing, but add the additional parameter data.reg_customer_id to your javascript under the payment data. The “data.reg_customer_id” parameter may represent the customer ID that you assign to each customer within your database. This ID will be paired with the token that DOKU gives in the status response.

The javascript with the additional parameter will generate the following payment form, which enables the customer to save their credit card.

Register Recurring Step 2

{
"res_approval_code":"844647",
"res_trans_id_merchant":"1706221359",
"res_amount":"30000.00",
"res_payment_date_time":"20160319114638",
"res_verify_score":"-1",
"res_verify_id":"",
"res_verify_status":"NA", "res_words":"7553a51a091775a2462eb9150c7135f4a8d58ff161db022ca42e0ef65666ebf0", "res_response_msg":"SUCCESS",
"res_mcn":"4***********1111",
"res_mid":"000100013000195",
"res_bank":"JPMORGAN CHASE BANK",
"res_response_code":"0000", "res_session_id":"4cf212f141a1d7fe672db93db75cc069,PRODUCTION", "res_payment_channel":"15", "res_bundle_token":"{"res_token_payment":"0bea1c1c653dbc8e1e6c24155c629fe237325a06",
 }
Credit Card Tokenization Payment form

Step 2: Generate and save the token during the first payment. When the customer has filled in their card details and clicked “Process Payment”, the data is sent to the DOKU server. Because the ‘data.reg_customer_id’ parameter has been added to the payment form, the DOKU server will create a token to pair with the Customer ID. If the customer checks the box next to “Save this credit card for faster checkout?”, the payment response to the Merchant server will include this token.

When the payment response is received, store it in your database for the next payment using the 1-Click service.

Register Recurring Step 3

<script type="text/javascript"> $(function() {
var data = new Object();
data.req_merchant_code = '1';
data.req_chain_merchant = 'NA';
data.req_payment_channel = '15';
data.req_transaction_id = '<?php echo $invoice ?>';
data.req_currency = '<?php echo $currency ?>';
data.req_amount = '<?php echo $amount ?>';
data.req_words = '<?php echo $words ?>';
data.req_form_type = 'full';
data.req_customer_id = '12124';
data.req_token_payment = '0bea1c1c653dbc8e1e6c24155c629fe237325a06';
getForm(data, ‘staging’); //for production environment, change ‘staging’ to ‘production’
});
</script>
Step 3: For subsequent payments, retrieve the token from your database and send it to the DOKU server. After a successful first payment, (assuming that the merchant has been correctly storing the Token data) only a slight modification needs to be made to the javascript. Add the extra parameter data.reg_token_payment , by using the token value that was obtained during the first payment:

The sample script will not generate another payment form, but will instead just display the “Process Payment” button.

Register Recurring Step 4

Step 4: Change method of payment in the payment request form. Once your customer has input their card data and clicked the “Process Payment” button, the data will be processed and DOKU will send a response containing the card ID. When you retrieve this data from your server, create the payment request following the instructions for regular credit card payments. However, when you make the payment request, you must change the method of payment to Doku_Api::doDirectPayment instead of Doku_Api::doPayment.

Installment integration
Below are the integration process that you need to go through to enable both types of installment:

Step 1: Create an installment form on your payment page Installment integration follows the same steps as a normal credit card payment, only with a few additional parameters. To start, please create an installment selection form on your payment page for your customer to choose their card issuer and preferred payment plan along with the doku-1.2.js credit card form. The installment form may look like this:

Installment page

Installment Data sample

$dataPayment = array(
'req_mall_id' => Doku_Initiate::$mallId,
'req_chain_merchant' => 'NA',
'req_amount' => '10000.00',
'req_words' => $words,
'req_purchase_amount' => '10000.00',
'req_trans_id_merchant' => $invoice_no,
'req_request_date_time' => date('YmdHis'),
'req_currency' => '360',
'req_purchase_currency' => '360',
'req_session_id' => sha1(date('YmdHis')),
'req_name' => $customer['name'],
'req_payment_channel' => 15,
'req_basket' => $basket,
'req_email' => $customer['data_email'],
'req_token_id' => $token,
'req_installment_acquirer' => ‘100’,  // from merchant
'req_tenor' => ‘12’,  // from merchant
'req_plan_id' => ‘001’ // from merchant,
'req_installment_off_us' => ‘O‘  // only for off-us transaction
)
Step 2: Send Payment Request There is no difference in the parameters sent from doku-1.2.js to your server, please do it as you would for a normal credit card payment. However, pair the credit card payment request parameters together with the installment information as you would need to combine the two when conducting the server-to-server payment charging process.

Step 3: Charge payment to DOKU server along with the installment parameters Send a payment charge request to DOKU using the usual DOKU library, only with the additional installment parameters. Installment_acquirer refers to the acquirer bank code, tenor is the number of months in the installment plan, plan_id is a promotion code the merchant has form the bank, and installment_off_us with value ‘O’ only for off-us transaction.

Authorize & Capture integration
The integration process for Authorize & Capture works as follow

Authorize
Autohorize payment data

$dataPayment = array(
'req_mall_id' => Doku_Initiate::$mallId, 'req_chain_merchant' => 'NA',
'req_amount' => '10000.00',
'req_words' => $words,
'req_purchase_amount' => '10000.00',
'req_trans_id_merchant' => $invoice_no,
'req_request_date_time' => date('YmdHis'),
'req_currency' => '360',
'req_purchase_currency' => '360',
'req_session_id' => sha1(date('YmdHis')),
'req_name' => $customer['name'],
'req_payment_channel' => 15,
'req_basket' => $basket,
'req_email' => $customer['data_email'],
'req_token_id' => $token
'req_authorize_expiry_date’ => ‘1440’ // from merchant, per minute (optional)
'req_payment_type’ => ‘A’,
)
To send a payment authorization request, follow the exact same steps as a normal credit card payment charging request, with additional parameters that you send during the server-to-server process

"req_authorize_expiry_date" refers to the time limit (in minutes) that you want to impose on authorizing a certain amount of the card limit; the maximum is 15 days. While the value ‘A’ for "req_payment_type" refers to an Authorize request. During this process DOKU will check whether there is still enough limit on the card to Authorize the amount. After successfully completing the Authorize process, you will receive an "approval_code" parameter. Store and pair it with your "trans_id_merchant" parameter to later complete the Capture process.

Capture
Capture payment data

$dataPayment = array(
'req_mall_id' => Doku_Initiate::$mallId,
'req_chain_merchant' => 'NA',
'req_amount' => '10000.00',
'req_words' => $words,
'req_trans_id_merchant' => $invoice_no,
'req_request_date_time' => date('YmdHis'),
'req_session_id' => sha1(date('YmdHis')),
'req_payment_channel' => 15,
'req_approval_code’ => ‘’  // based on authorize transaction
)
To capture, simply send a server-to-server charging request to DOKU as shown by example below. You do not have to follow the full credit card steps since the customer does not have to fill in their card details anymore and getToken process can be bypassed.

DOKU Wallet Integration
Step 1

<script src="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.pack.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css" rel="stylesheet">
<script src="http://staging.doku.com/doku-js/assets/js/doku-1.2.js"></script>
<link href="http://staging.doku.com/doku-js/assets/css/doku.css" rel="stylesheet">
DOKU Wallet have similar way to integrate like credit card. To get started on your integration, follow these steps one by one by pasting the template scripts onto your website. The DOKU payment form is saved in HTML format; the template script acts as a placeholder for where the payment form will appear on your page. Prepare your HTML pages as seen in the template, and customize accordingly.

Step 2

<?php require_once('../Doku.php');
Doku_Initiate::$sharedKey = ‘<Put Your Shared Key Here>’;
Doku_Initiate::$mallId = '<Put Your Merchant Code Here>';
$invoice = 'invoice_1458123951’;
$params = array('amount' => '10000.00', 'invoice' => $invoice, 'currency' => '360');
$words = doku_Library::doCreateWords($params);
?>
Doku Wallet integration comprises 3 steps:

Step 1: Insert JavaScript

Insert the doku-1.2.js, fancybox.js and fancybox.css onto your website’s payment page, along with your custom style.

Step 2: Initiate JavaScript parameters Initialize the payment form by creating the words using function sample

<script type="text/javascript">
$(function() {
var data = new Object();
data.req_merchant_code = '1';
data.req_chain_merchant = 'NA';
data.req_payment_channel = '04';
data.req_transaction_id = '<?php echo $invoice ?>';
data.req_currency = '<?php echo $currency ?>';
data.req_amount = '<?php echo $amount ?>';
data.req_words = '<?php echo $words ?>';
data.req_form_type = 'full';
getForm(data, ‘staging’); //for production environment, change ‘staging’ to ‘production’
});
</script>
And add the example script on to your webpage.

Step 3

<form action="charge.php" method="POST" id="payment-form">
    <div doku-div='form-payment'>
        <input id="doku-token" name="doku-token" type="hidden" />
        <input id=" doku-pairing-code" name="doku-pairing-code" type="hidden" />
    </div>
</form>
Step 3: Create payment form Insert the template script where you wish the payment form to appear on your website. When completed correctly, the payment form should appear as seen below, and you may start receiving payments immediately. The DOKU script only provides the two fields to be filled in by the customer. All other parts of the payment page, including ‘Process Payment’ button are customizable to your needs.

DOKU Wallet login

Once your customer has input their DOKU ID and signed in to their account, their balance and payment options will appear in a pop-pup window, which follows the DOKU template, like this:

DOKU Wallet payment form

The customer may choose to pay with their existing cash balance and may apply a Voucher or Promo Code if he/she has a valid one. The customer may also choose to pay with the Credit Card that has been linked to their DOKU Wallet. Note however, that to activate the credit card option, further process is required. If the Credit Card option is not yet activated for you and you would like to do so, please contact DOKU.

DOKU Wallet cc payment form

<?php require_once('../Doku.php');
Doku_Initiate::$sharedKey = ‘<Put Your Shared Key Here>’;
Doku_Initiate::$mallId = '<Put Your Merchant Code Here>';

$token = $_POST['doku-token'];
$pairing_code = $_POST['doku-pairing-code'];
$invoice_no = $_POST['doku-invoice-no'];
$params = array('amount' => '10000.00', 'invoice' => $invoice_no, 'currency' => '360', 'pairing_code' => $pairing_code, 'token' => $token);
$words = Doku_Library::doCreateWords($params);
$basket[] = array('name' => 'sayur', 'amount' => '10000.00', 'quantity' => '1', 'subtotal' => '10000.00');
$customer = array('name' => 'TEST NAME', 'data_phone' => '08121111111', 'data_email' => 'test@test.com', 'data_address' => 'bojong gede #1 08/01');
$data = array('req_token_id' => $token, 'req_pairing_code' => $pairing_code, 'req_customer' => $customer, 'req_basket' => $basket, 'req_words' => $words);

$responsePrePayment = Doku_Api::doPrePayment($data);
if($responsePrePayment->res_response_code == '0000'){     //prepayment success

$dataPayment = array('req_mall_id' => '1', 'req_chain_merchant' => 'NA', 'req_amount' => '10000.00', 'req_words' => $words, 'req_purchase_amount' => '10000.00', 'req_trans_id_merchant' => $invoice_no, 'req_request_date_time' => date('YmdHis'), 'req_currency' => '360', 'req_purchase_currency' => '360', 'req_session_id' => sha1(date('YmdHis')), 'req_name' => $customer['name'], 'req_payment_channel' => 04, 'req_basket' => $basket, 'req_email' => $customer['data_email'], 'req_token_id' => $token);

$result = Doku_Api::doPayment($dataPayment);
if($result->res_response_code == '0000'){
    echo 'SUCCESS';  //success
    }else{
        echo 'FAILED';   //failed
            }
}else{     //prepayment fail
When the customer clicks the “Process Payment” button, the DOKU server will process the data and send a response to the browser. The browser will then post the data to the merchant server, according to the URL set in your action form. You can retrieve the posted data from the form within your server. Then send the payment request to the DOKU server to be processed using our function sample

After this, you may display the result on your browser for the customer to see.

DOKU Wallet finish form

Virtual Account Integration
Virtual Account payment process comprise 2 asynchronous process: Generate Payment Code (Virtual Account Number), and Payment Process.

<?php require_once('../Doku.php');
date_default_timezone_set('Asia/Jakarta');
Doku_Initiate::$sharedKey = <Put Your Shared Key Here>;
Doku_Initiate::$mallId = <Put Your Merchant Code Here>

$params = array('amount' => $_POST['amount'], 'invoice' => $_POST['trans_id'], 'currency' => $_POST['currency']);
$words = Doku_Library::doCreateWords($params);
$customer = array('name' => 'TEST NAME','data_phone' => '08121111111', 'data_email' => 'test@test.com', 'data_address' => 'bojong gede #1 08/01');
$dataPayment = array('req_mall_id' => $_POST['mall_id'], 'req_chain_merchant' => $_POST['chain_merchant'], 'req_amount' => $params['amount'], 'req_words' => $words, 'req_trans_id_merchant' => $_POST['trans_id'], 'req_purchase_amount' => $params['amount'], 'req_request_date_time' => date('YmdHis'), 'req_session_id' => sha1(date('YmdHis')), 'req_email' => $customer['data_email'], 'req_name' => $customer['name'], 'req_basket' => 'sayur,10000.00,1,10000.00;', 'req_address' => 'Jl Kembang 1 No 5 Cilandak Jakarta', 'req_mobile_phone' => '081987987999', 'req_expiry_time' => '360');

$response = Doku_Api::doGeneratePaycode($dataPayment);
if($response->res_response_code == '0000'){
        echo 'GENERATE SUCCESS -- ';
}else{
        echo 'GENERATE FAILED -- ';
} ?>
Generate Payment Code
Payment Code generated by DOKU will have total 16 digits length. The payment code consist of 5 digits or 8 digits prefix from Bank/DOKU, continued with 11 digits or 8 digits number generated by DOKU. Both of request type (8 digits or 11 digits payment code) have different endpoint / URL.

Step 1: Generate Payment Code By using the our function sample, you can make a payment code request with ease. The request process is performed host to host.

You can set payment code expiry time in parameter ‘req_expiry_time’. Exceeding this time limit will render the payment code invalid. You may set the time limit however you like, in minute format.

 If you do not send the `req_expiry_time` parameter, DOKU will set it at the default time of 360 minutes (6 hours).
Sample of generate payment code response

{
"res_pay_code":"62700000003",
"res_pairing_code":"290316110837531987",
"res_response_msg":"SUCCESS",
"res_response_code":"0000"
}
Step 2: Receive DOKU response.
DOKU will respond generate payment code request in JSON format. Response contain payment code generated (8 digits or 11 digits).

Step 3: Display Payment Code in Merchant's browser
It is suggested to display payment code that already combined with 5 digits or 8 digits prefix for each payment channel.

Receive Payment Notification
Sample of virtual account payment notification

PAYMENTDATETIME=20160329110948
PURCHASECURRENCY=360
PAYMENTCHANNEL= FROM DOKU
AMOUNT=10000.00
PAYMENTCODE=00100000029
WORDS=01d9b362d3c1b80ff9196c6a565c49e5d9b03b8a
RESULTMSG=SUCCESS
TRANSIDMERCHANT=ZA912172
BANK=PERMATA
STATUSTYPE=P
APPROVALCODE=068992
RESPONSECODE=0000
SESSIONID=7b6647973dd13211a7fcf42eba79acea68aa69a1
Step 1: After the customer has made a payment, DOKU will send a payment notification containing the payment parameters to your server.

Sample of handling payment notification

Step 2: Notify DOKU server that Payment Notification has been received by responding "CONTINUE".

Mandiri Clickpay Integration
Internet banking payment channel supported in Merchant Hosted currently only Mandiri Clickpay. To get started on your integration, follow these steps one by one by pasting the template scripts onto your website. The DOKU payment form is saved in HTML format; the template script acts as a placeholder for where the payment form will appear on your page. Prepare your HTML pages as seen in the template, and customize accordingly. The form you create in this step will receive the Mandiri Clickpay input from the customer.

<script src="doku-1.2.js"></script>
<link href="http://staging.doku.com/doku-js/assets/css/doku.css" rel="stylesheet">
<script src='http://staging.doku.com/doku-js/assets/js/jquery.payment.min.js'></script>
Step 1: Insert the doku-1.2.js onto your website’s payment page, along with your custom style.

js URL:

Environment	URL
staging	http://staging.doku.com/doku-js/assets/js/jquery.payment.min.js
production	https://pay.doku.com/doku-js/assets/js/doku-1.2.js?version=1497508770
css URL:

Environment	URL
staging	http://staging.doku.com/doku-js/assets/css/doku.css
production	https://pay.doku.com/doku-js/assets/css/doku.css
Step 2

<script type="text/javascript">
    jQuery(function($) {
        $('.cc-number').payment('formatCardNumber');
        var challenge3 = Math.floor(Math.random() * 999999999);
        $("#CHALLENGE_CODE_3").val(challenge3);
    });

    $(function() {
        var data = new Object();
        data.req_cc_field = 'cc_number';
        data.req_challenge_field = 'CHALLENGE_CODE_1';
        dokuMandiriInitiate(data);
    });
</script>
 Please change URL when migrating to Production environment
Step 2: Initialize the payment form by adding the following example script onto your webpage.

Step 3

<form method="post" action="../example/mandiri-clickpay-charge.php">
<div id="mandiriclickpay" class="channel">
    <div class="list-chacode">
        <ul>
            <li>
                <div class="text-chacode">Challenge Code 1</div>
                <input type="text" id="CHALLENGE_CODE_1" name="CHALLENGE_CODE_1" readonly="true" required/>
                <div class="clear"></div>
            </li>
            <li>
                <div class="text-chacode">Challenge Code 2</div>
                <div class="num-chacode">0000100000</div>
                <input type="hidden" name="CHALLENGE_CODE_2" value="0000100000"/>
                <div class="clear"></div>
            </li>
            <li>
                <div class="text-chacode">Challenge Code 3</div>
                <div class="num-chacode" id="challenge_div_3"></div>
                <input type="hidden" name="CHALLENGE_CODE_3" id="CHALLENGE_CODE_3" value=""/>
                <div class="clear"></div>
            </li>
            <div class="clear"></div>
        </ul>
    </div>
    <div class="validasi">
        <div class="styled-input fleft width50">
            <input type="text" required="" name="response_token">
            <label>Respon Token</label>
        </div>
        <div class="clear"></div>
    </div>
    <input type="hidden" name="invoice_no" value="invoice_1458547984">
    <input type="button" value="Process Payment" class="default-btn" onclick="this.form.submit();">
</div>
</form>
Step 3: Insert the template script where you wish the payment form to appear on your website.

Step 4: When completed correctly, the payment form should appear as seen below, and you may start receiving payments using Mandiri Clickpay immediately.

Mandiri Click Pay Payment form

Once your customer has input their Mandiri Clickpay data and clicked the “Process Payment” button, the data will be processed on DOKU. The DOKU server responds to the browser, and the data will be posted to the merchant server, according to the URL set in you action form.

Step 5

Step 5: You can retrieve the posted data from the form within your server. Then send the payment request to the DOKU server to be processed using our function sample.

Response sample

{
"res_response_msg":"SUCCESS",
"res_transaction_code":"d4efbb8c4ebb9a3597c05aa32f2b341e77f98e63",
"res_mcn":"4***********1111",
"res_approval_code":"1234",
"res_trans_id_merchant":"1706332101",
"res_payment_date":"20160319184828",
"res_bank":"MANDIRI CLICK PAY",
"res_amount":"30000.00",
"res_message":"PAYMENT APPROVED",
"res_response_code":"0000",
"res_session_id":"50d240541f4d8d7565b18cb5ca93a660"
}
Step 6: DOKU server will send payment response in JSON.

API
Endpoint
Action	URL	Description
prePayment	http://staging.doku.com/api/payment/PrePayment	
payment	http://staging.doku.com/api/payment/paymentMip	
directPayment	http://staging.doku.com/api/payment/PaymentMIPDirect	
generateCode	http://staging.doku.com/api/payment/DoGeneratePaycodeVA	for 8 digits request
http://staging.doku.com/api/payment/doGeneratePaymentCode	for 11 digits request
Request Parameters
 Please note that parameters in bold red font is mandatory, and parameters in normal font is optional
 Definition in "Type" column: A=Alphabet, AN=Alphanumeric, ANS=Alphanumeric & Special Character
Name	Type	Length	Description
req_mall_id or req_merchant_code	N		Given by DOKU. Use "req_mall_id" for VA or Mandiri Clickpay payment channel. Use "req_merchant_code" for Credit Card or DOKU Wallet payment channel.
req_chain_merchant	N		Given by DOKU, if not using Chain, default value is "NA"
req_amount	N	12.2	Total amount. Eg:10000.00
req_purchase_amount	N	12.2	Total amount. Eg:10000.00
req_trans_id_merchant or req_transaction_id	AN	…30	Transaction ID from Merchant. Use "req_trans_id_merchant" for VA or Mandiri Clickpay payment channel. Use "req_transaction_id" for Credit Card or DOKU Wallet payment channel.
req_words	AN	…200	Hashed key combination encryption (use SHA1 method). For credit card, combined parameters value in order: req_amount+req_merchant_code+(shared key)+req_transaction_id+req_purchase_currency+token_id+pairing_code. For Mandiri ClickPay, combined parameters value in order: req_amount+req_mall_id+(shared key)+req_trans_id_merchant+req_currency
req_request_date_time	N	14	YYYYMMDDHHMMSS
req_currency	N	3	ISO3166 , numeric code
req_purchase_currency	N	3	ISO3166 , numeric code
req_session_id	AN	…48	Session ID from Merchant
req_name	AN	…50	Travel arranger name / buyer name
req_email	ANS	…100	Customer email
req_basket	ANS	…1024	Show transaction description. Use comma to separate each field and semicolon for each item. Item 1, 1000.00.,2,20000,00;item2,15000.00,2,30000.00
token_id	AN		Sent by DOKU during getToken process
req_shipping_address	ANS	…100	Shipping address contains street and number
req_shipping_city	ANS	…100	City name
req_shipping_state	AN	…100	State / province name
req_shipping_country	A	2	ISO3166, alpha-2. Mandatory for credit card and DOKU Wallet payment
req_shipping_zip_code	N	…10	Zip Code. Mandatory for credit card and DOKU Wallet payment
req_payment_channel	N	2	See payment channel code
req_address	ANS	…100	Home address contains street and number. Mandatory for credit card and DOKU Wallet payment
req_city	ANS	…100	City name
req_state	AN	…100	State / province name
req_country	A	2	ISO3166, alpha-2
req_zip_code	N	…10	Zip Code
req_mobile_phone	ANS	…15	Home Phone
req_work_phone	ANS	…13	Work Phone / Office Phone
req_birth_date	N	…8	YYYYMMDD
req_form_type	AN		Full/Inline
req_domain_valid	ANS		Merchant's website domain
req_timeout	N		Timeout transactions in minutes
req_bin_filter	ANS		Example: "42*1", "4?3??3","411111","5*"
req_expiry_time	N		VA number expiry time. Default is '360'
Additional Parameters for Airline Merchant
Name	Type	Length	Description
req_flight	N	2	01 for Domestic, 02 for International
req_flight_type	N	1	0 : One Way, 1 : Return, 2 : Transit, 3 : Transit & Return, 4 : Multiple Cities
req_booking_code	AN	…20	Booking code generated by Airline
req_vat	N		Total VAT. Eg: 10000.00
req_insurance	N		Total Insurance. Eg: 10000.00
req_fuel_surcharge	N		Total fuel surcharge. Eg: 10000.00
req_route	AN	…50	List of route using format XXX-YYY (from XXX to YYY). E.g. : CGK-DPS
req_flight_date	N	8	List of flight date using format YYYYMMDD
req_flight_time	N	6	List of flight time using format HHMMSS
req_flight_number	AN	…30	List of flight number using IATA Standard. XXYYYY (XX = Airline Name, YYYY = Flight Number)
req_passenger_name	AN	…50	List of passenger name in one booking code
req_passenger_type	AN	1	List of passenger type in one booking. A : Adult, C : Child
req_ff_number	AN	…1024	Frequent Flyer Number
req_thirdparty_status	ANS	1	0 : Travel Arranger joins the flight, 1 : Travel Arranger does not join the flight
Additional Parameters for Credit Card Installment
Name	Type	Length	Description
req_installment_acquirer	N	3	Acquirer code for installment
req_tenor	N	2	Number of month to pay the installment
req_plan_id	N	3	Promotion ID from the bank for the current merchant
req_installment_off_us	AN	1	Default value null for on-us installment. For off-us installment send "O"
Additional Parameters for Tokenization
Name	Type	Length	Description
req_customer_id	AN	…16	Merchant’s customer identifier
req_token_payment			
Additional Parameters for Authorize & Capture
Name	Type	Length	Description
req_authorize_expiry_date	N	6	Expiry time of the payment Authorization (in minutes). Maximum is 15 days
req_payment_type	N	…10	Please enter ‘A’ for Authorize
req_approval_code		Received from DOKU during Authorize process	
Other API & Callback
 Please note that parameters in bold red font is mandatory, and parameters in normal font is optional. If optional parameter sent in invalid format or length, DOKU will set value to NULL.
 Definition in "Type" column: A=Alphabet, AN=Alphanumeric, ANS=Alphanumeric & Special Character
Other Payment Request
Endpoint	HTTP Method	Definition
/Suite/ReceiveMIP	POST	To check the status of a Transaction, Merchant server send request to DOKU server where DOKU server will response with Transaction Status in XML format.
Other Payment Request Parameter
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. If not using Chain, use value: NA
AMOUNT	N	12.2	Total amount. Eg: 10000.00
PURCHASEAMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT For transaction with currency other than 360 (IDR), use:
AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+CURRENCY
For Shared Key, refer to Shared Key Hashed Value
REQUESTDATETIME	N	14	YYYYMMDDHHMMSS
CURRENCY	N	3	ISO3166, numeric code
PURCHASECURRENCY	N	3	ISO3166, numeric code
SESSIONID	AN	48	Merchant can use this parameter for additional validation, DOKU will return the value in other response process.
NAME	AN	128	Customer / Buyer name
EMAIL	ANS	100	Customer / Buyer email
USERIDKLIKBCA	ANS	12	Customer KLIKBCA user ID. Mandatory for KLIKBCA payment
ADDITIONALDATA	ANS	1024	Custom additional data for specific merchant use
BASKET	ANS	1024	Show transaction description. Use comma to separate each field and semicolon for each item. E.g. Item1,1000.00,2,20000.00;item2,15000.00,2,30000.00
PAYMENTCHANNEL	N	2	See Payment Channel Code
EXPIRYTIME	N	14	Expiry time for BNI Yap bill. Format: YYYYMMDDHHMMSS
Other Payment Response sample

<?xml version="1.0" encoding="UTF-8"?>
<PAYMENT_RESPONSE>   
<RESPONSECODE>0000</RESPONSECODE>
<RESPONSEMSG>SUCCESS</RESPONSEMSG>
</PAYMENT_RESPONSE>
Other Payment Response
Request will be responded in XML format.

Parameter	Type	Length	description
RESPONSECODE	N	4	Request response code
RESPONSEMSG	A	..20	Request message
Check Status Request
Endpoint	HTTP Method	Definition
/Suite/CheckStatus	POST	To check the status of a Transaction, Merchant server send request to DOKU server where DOKU server will response with Transaction Status in XML format.
Check Status Request Parameter
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. By default NA
SESSIONID	AN	48	Original value from Sale Request
TRANSIDMERCHANT	AN	40	Transaction ID from Merchant
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
1. MALLID+SHAREDKEY+TRANSIDMERCHANT
2. Has Rate or Has Purchase Currency and Purchase Currency not equals to 360:
MALLID+SHAREDKEY+TRANSIDMERCHANT+PURCHASECURRENCY
Refer to Shared Key Hashed Value
PAYMENTCHANNEL	2		See Payment Channel Code section
CURRENCY	N	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
PAYMENTTYPE	N		AUTHORIZATION, or CAPTURE. If not sent, last transaction will be responded
Check Status Response
DOKU will echo payment status in XML format.

Check Status Response (Sample)

Parameter	Type	Length	Description
AMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
WORDS	AN	200	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order: AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS
For transaction with currency other than 360 (IDR), use : AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS+CURRENCY
Refer to Shared Key Hashed Value
RESPONSECODE*	N	4	0000: Success, others Failed
APPROVALCODE	AN	20	Transaction number from bank
RESULTMSG*	A	20	SUCCESS or FAILED
PAYMENTCHANNEL	N	2	See payment channel code list
PAYMENTCODE	N	8	Virtual Account identifier for VA transaction. Has value if using Channel that has payment code.
SESSIONID	AN	48	DOKU will return the value from Payment Request.
BANK	AN	100	Bank Issuer
MCN	ANS	16	Masked card number
PAYMENTDATEANDTIME	N	14	YYYYMMDDHHMMSS
VERIFYID	N	30	Generated by Fraud Screening (RequestID)
VERIFYSCORE	N	3	-1 or 0 to 100
VERIFYSTATUS	A	10	APPROVE / REJECT / REVIEW / HIGHRISK / NA
CURRENCY	N	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
BRAND	A	10	VISA / MASTERCARD
CHNAME	AN	50	Cardholder Name
THREEDSECURESTATUS	A	5	TRUE or FALSE
LIABILITY	A	10	CUSTOMER / MERCHANT / NA
EDUSTATUS	A	10	Manual Fraud Review, value : APPROVE / REJECT / NA (default)
* Main identifier of transaction success / failed

Inquiry Callback
Inquiry is used only for Direct Inquiry Virtual Account flow. Merchant should inform the URL where DOKU server will send inquiry request. You can configure the URL in "Identify URL" on DOKU Merchant Dashboard Settings. Example: http://www.yourwebsite.com/directory/DOKU_redirect.php

Inquiry Parameters Sent
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. By default NA
PAYMENTCHANNEL	N	2	See Payment Channel Code
PAYMENTCODE	N	8	Virtual Account identifier for VA transaction
WORDS	AN	200	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
MALLID+PAYMENTCODE
Refer to Shared Key Hashed Value
Merchant Inquiry Response
DOKU will expect response Inquiry from merchant in XML format with these parameters:

Inquiry Response (Sample)

Parameter	Type	Length	Description
PAYMENTCODE	N	16	Virtual Account identifier for VA transaction
AMOUNT	N	12.2	Total amount. If open amount, please set 0. Eg: 10000.00
PURCHASEAMOUNT	N	12.2	Total amount. If open amount, please set 0. E.g.: 10000.00
MINAMOUNT	N	12.2	If merchant implement open amount scheme, it is suggested to set this parameter. e.g.: 10000.00
MAXAMOUNT	N	12.2	If merchant implement open amount scheme, it is suggested to set this parameter. e.g. 500000.00
TRANSIDMERCHANT	AN	48	Transaction ID from Merchant
WORDS	AN	254	Hashed key combination encryption (use SHA1 method). The hashed key generated from combining these parameters value in this order: AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT
Refer to Shared Key Hashed Value
REQUESTDATETIME	N	14	YYYYMMDDHHMMSS
CURRENCY	N	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
SESSIONID	AN	48	DOKU will return the value from Payment Request
NAME	AN	50	Customer / Buyer name
EMAIL	ANS	100	Customer / Buyer email
BASKET	ANS	1024	Show transaction description. Use comma to separate each field and semicolon for each item. E.g. Item1,1000.00,2,20000.00;item2,15000.00,2,30000.00
ADDITIONALDATA	ANS	1024	Custom additional data for specific merchant use
RESPONSECODE	N	4	3000 = Bill not found
3001 = Decline
3002 = Bill already paid
3004 = Account number / Bill was expired
3006 = VA Number not found
0000 = Success
9999 = Internal Error / Failed
Capture Request
Endpoint	HTTP Method	Definition
/Suite/CaptureRequest	POST	Capture is to confirm Authorize transaction.
Capture Request Parameter
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. By default NA
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
APPROVALCODE	N	20	Transaction ID from Bank
AMOUNT	N	12.2	Total amount. e.g.: 10000.00
PURCHASEAMOUNT	N	12.2	Total amount. e.g.: 10000.00
CURRENCY	AN	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
SESSIONID	AN	48	Original value from Authorization request
WORDS	N	254	Hashed key generated from combining these parameters value in this order : MALLID++TRANSIDMERCHANT+SESSIONID
Refer to Shared Key Hashed Value
PAYMENTCHANNEL	AN	2	Only for Credit Card (15)
Capture Response
Capture response sample

<?xml version="1.0"?>
<PAYMENT_STATUS>
<AMOUNT></AMOUNT>
<TRANSIDMERCHANT></TRANSIDMERCHANT>
<WORDS></WORDS>
<RESPONSECODE></RESPONSECODE>
<APPROVALCODE></APPROVALCODE>
<RESULTMSG></RESULTMSG>
<PAYMENTCHANNEL></PAYMENTCHANNEL>
<SESSIONID></SESSIONID>
<MCN></MCN>
<PAYMENTDATETIME></PAYMENTDATETIME>
<CURRENCY></CURRENCY>
<PURCHASECURRENCY></PURCHASECURRENCY>
</PAYMENT_STATUS>
Parameter	Type	Length	Description
AMOUNT	N	12.2	Total amount. Eg: 10000.00
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
WORDS	AN	200	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order: AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG
For transaction with currency other than 360 (IDR), use :
AMOUNT+MALLID+SHAREDKEY+TRANSIDMERCHANT+RESULTMSG+VERIFYSTATUS+CURRENCY
Refer to Shared Key Hashed Value
RESPONSECODE*	N	4	0000: Success, others Failed
APPROVALCODE	AN	20	Transaction number from bank
RESULTMSG*	A	20	SUCCESS or FAILED
PAYMENTCHANNEL	N	2	See Payment Channel Code
SESSIONID	AN	48	DOKU will return the value from Payment Request.
MCN	ANS	16	Masked card number
CURRENCY	N	3	ISO3166 , numeric code
PURCHASECURRENCY	N	3	ISO3166 , numeric code
* Main identifier of transaction success / failed

Void Request
Endpoint	HTTP Method	Definition
/Suite/VoidRequest	POST	Void is a feature to cancel successful unsettled transaction.
Void Request Parameter
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. By default NA
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
SESSIONID	AN	48	Original value from Sale Request
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
MALLID+SHAREDKEY+TRANSIDMERCHANT+SESSIONID
Refer to Shared Key Hashed Value
PAYMENTCHANNEL	N	2	See Payment Channel Code list
Void Response sample

  SUCCESS

or

  FAILED;Transaction Not Found
Void Response
Void response will be in plain text.

Response	Description
SUCCESS	Void request success
FAILED;[error message]	error message: "Transaction Not Found" or "Transaction Cannot Void"
Refund Request
Endpoint	HTTP Method	Definition
/Suite/DoRefundRequest	POST	Refund allows Merchant to Refund Sale & Installment on-us Transaction
Refund Request Parameter
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
CHAINMERCHANT	N	8	Given by Doku. By default NA
REFIDMERCHANT	N	30	New Refund Transaction ID from Merchant
TRANSIDMERCHANT	AN	30	Original Transaction ID from Merchant
APPROVALCODE	AN	20	Transaction number from Bank
AMOUNT	N	12.2	Total VOID / REFUND amount
CURRENCY	N	3	ISO3166, numeric code
REFUNDTYPE	N	2	01 = Full Refund, 02 = Partial Refund Credit (Credit to customer account), 03 = Partial Refund Debit (debit from customer account)
SESSIONID	AN	48	Merchant can use this parameter for additional validation, DOKU will return the value in other response process
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
AMOUNT+MALLID+SHAREDKEY+REFIDMERCHANT+SESSIONID
For transaction with currency other than 360 (IDR), use :
AMOUNT+MALLID+SHAREDKEY+REFIDMERCHANT+SESSIONID+CURRENCY
Refer to Shared Key Hashed Value
REASON	ANS	256	Reason for Refund
BANKDATA	ANS	256	Additional Data
DATA1	ANS	256	Additional Data
DATA2	ANS	256	Additional Data
DATA3	ANS	256	Additional Data
DATA4	ANS	256	Additional Data
Refund Response
Refund Response Sample

Parameter	Description
RESPONSECODE	Refund response code
RESPONSEMSG	Refund status
TRANSIDMERCHANT	Transaction ID from Merchant
REFNUM	Reference number
SESSIONID	Refund session ID
REFIDMERCHANT	Refund ID from Merchant
Cancellation Request
Endpoint	HTTP Method	Definition
/Suite/DoCancelRequest	POST	Cancellation allows Merchant to cancel Sale transaction regardless of its settlement status
Cancellation Request Parameter
Parameter	Type	Length	Description
MALLID	N	10	Merchant ID given by Doku
REFIDMERCHANT	N	30	New Refund Transaction ID from Merchant
TRANSIDMERCHANT	AN	30	Original Transaction ID from Merchant
APPROVALCODE	AN	20	Transaction number from Bank
AMOUNT	N	12.2	Total VOID / REFUND amount
CURRENCY	N	3	ISO3166 , numeric code
REFUNDTYPE	N	2	If Partial Refund Debit (debit from customer account), it’s mandatory to enter ‘03’. Otherwise, value in this parameter is not needed
SESSIONID	AN	48	Merchant can use this parameter for additional validation, DOKU will return the value in other response process
WORDS	AN	254	Hashed key combination encryption. The hashed key generated from combining these parameters value in this order:
AMOUNT+MALLID+SHAREDKEY+REFIDMERCHANT+SESSIONID
For transaction with currency other than 360 (IDR), use :
AMOUNT+MALLID+SHAREDKEY+REFIDMERCHANT+SESSIONID+CURRENCY
Refer to Shared Key Hashed Value
REASON	ANS	256	Reason for Refund
BANKDATA	ANS	256	Additional Data
DATA1	ANS	256	Additional Data
DATA2	ANS	256	Additional Data
DATA3	ANS	256	Additional Data
DATA4	ANS	256	Additional Data
Refund Response
Cancellation Response (Sample)

Parameter	Type	Length	Description
TRANSIDMERCHANT	AN	30	Transaction ID from Merchant
RESPONSECODE	N	4	0000: Success, others Failed
RESPONSEMSG	A	20	VOIDED / REFUNDED / FAILED
REFNUM	AN	6	Transaction number from bank
SESSIONID	AN	48	Original value from Sale Request.
REFIDMERCHANT	AN	100	New Refund Transaction ID from Merchant
Response Code
This response codes are not meant for customer. It’s for merchant’s benefits. Merchant must always treat declined transactions as the customer is required to contact their Bank Issuer for the declined credit card. This data is very confidential. Do not reproduce in any kind to public view. Fail to do so will void merchant’s account.

DOKU General Response Code
Response Code	Description
0000	Successful approval
0001	Failed
5501	Payment channel not registered
5502	Merchant Payment Channel is disabled
5503	Maximum attempt 3 times
5504	WORDS not match
5505	Invalid parameter
5506	Notify failed
5507	Invalid parameter detected / Customer click cancel process
5508	Re-enter transaction
5509	Payment code already expired
5510	Cancel by customer
5511	Not an error, transaction has not been paid
5512	Insufficient parameter
5513	Voided by system
5514	High Risk or Rejected by fraud system
5515	Duplicate PNR
5516	Transaction not found
5517	Error in authorization process
5518	Error parsing XML
5519	Stop at 3D secure page
5520	Register / Scheduler Transaction failed
5521	Invalid merchant
5522	Rates were not found
5523	Failed to get transaction status
5524	Failed to reverse transaction
5525	Transaction can not be processed
5526	Transaction timeout to or from acquirer
5527	Transaction will be processed as Off Us installment
5529	Invalid merchant
5530	Internal server error
5531	Pairing code does not exist
5532	Invalid payment channel
5533	Failed to inquiry list of fund
5534	Invalid pairing code
5535	Invalid token
5536	Time out
5537	Invalid currency
5538	Invalid purchase currency
5539	3D Secure enrollment check failed
5540	3D Secure authentication failed
5541	Form type is not valid
5542	Duplicate transaction ID
5543	Please check 3D Secure result
5544	Failed to delete token
5545	Failed to void
5547	BIN is not allowed in promo
5548	Invalid parameter
5549	Invalid domain
5550	Invalid IP address
5551	Merchant does not use 1-click service
5552	Invalid token expire
5553	Failed to tokenize / generate merchant key
5554	Off-Us Reward process
5555	Undefined error / Failed to decrypt
5556	Tokenization Failed
5557	Merchant does not have tokenization credential
5558	Cannot capture to System
5559	Batch list is null
5560	Batch ID is already available
5561	OCO ID is not exist
5562	Failed settlement
5563	Failed parsing PARES
5564	Batch ID not found in transaction
5565	Feature for master merchant id
5566	Invalid amount parameter captured
5567	Failed do re-notify
5568	Failed Refund
5569	Void/Refund amount is not Valid
5570	Transaction is canceled by merchant
5571	Failed Register Paycode
5572	No response
5573	Failed create bill
5574	Merchant not found or not active
5575	Transaction already voided
003D	Wrong OTP or customer did not continue the transaction at 3D Secure page
00BA	Blocked by Acquirer
00BB	BIN blocking, because card origin was not allowed to go through the payment
0098	3D Secure failure -- The card does not support 3D Secure
00UA	Failed 3DS authentication, could be caused by issuer or customer
00RJ	Reject from Fraud Screening System
Credit Card Response Code
Credit card transaction response code can be checked in this URL: https://developer.visa.com/request_response_codes

 DOKU will add “00” prefix in front of response code. Eg : Do Not Honor (05) will be 0005.
Mandiri Clickpay Response Code
Response Code	Description
0001	Internal system error: cannot parse message
0002	Internal system error: unmatched signature hash
0003	Internal system error: Cannot process message
0004	Internal system error: Error on field
0005	Internal system error: Transaction not found
0006	Internal system error: Create VPA response error
0101	Internal system error: Create velis-authenticator message
0102	Internal system error: Runtime try/catch error when creating VTCPStream
0103	Internal system error: Cannot connect to velis-authenticator
0104	Internal system error: Send request to velis-authenticator failed
0105	Internal system error: Waiting response from velis-authenticator failed
0106	Internal system error: Read response from velis-authenticator failed
0107	Internal system error: Parse response from velis-authenticator failed
0108	Internal system error: Signature key from velis-authenticator is invalid
1101	User not registered: Channel not register in database (not found)
1102	User not registered: User not active
1103	User not registered: User has deleted
1104	User not registered: User not found
1105	User not registered: Channel for User not active
1106	User not registered: Channel for User has deleted - no access
1107	User not registered: Channel for User not register / not found
1108	User has blocked: User has disabled
1109	User has blocked
1110	User has blocked: Channel for User has disabled
1111	User has blocked: Channel for User has blocked
1112	User already activated: User has invalid status (or already active)
1113	User already activated: Channel for User has invalid status (or already active)
1114	Invalid token: Token of User not active
1115	Invalid token: Token of User has disable
1116	Invalid token: Token of User has deleted
1117	Invalid token: Token of User not found
1118	Invalid token: Method CR not allowed for Token of User
1119	Invalid token: Method RO not allowed for Token of User
1120	Invalid token: Method SG not allowed for Token of User
1121	Invalid token: Device Token Type not valid (only support VS = VASCO Token)
1122	Invalid token response: Code Not Verified
1123	Invalid token response: Code Replay Attempt
1124	Invalid token response: Challenge Too Small
1125	Invalid token response: Challenge Too Long
1126	Invalid token response: Challenge Check Digit Wrong (Host Check Challenge Mode)
1127	Invalid token response: Challenge Character Not Decimal
1128	Invalid token response: Challenge Corrupt (Host Check Challenge Mode)
1129	Invalid token response: Response Length Out of Bounds
1130	Invalid token response: Response Too Small
1131	Invalid token response: Response Too Long
1126	Invalid token response: Challenge Check Digit Wrong (Host Check Challenge Mode)
1127	Invalid token response: Challenge Character Not Decimal
1128	Invalid token response: Challenge Corrupt (Host Check Challenge Mode)
1129	Invalid token response: Response Length Out of Bounds
1130	Invalid token response: Response Too Small
1131	Invalid token response: Response Too Long
1132	Invalid token response: Response Check Digit Wrong
1133	Invalid token response: Response Character Not Decimal
1134	Invalid token response: Response Character Not Hexadecimal
1135	Invalid token response: Token Authentication Failed
1199	Receive error response from VA
0201	Internal system error: Create DSP-ISO message failed
0202	Internal system error: No active DSPSession
0203	Internal system error: Cannot send request to DSP-Silverlake
0204	Internal system error: Waiting response from DSP-Silverlake
0205	Internal system error: Read response from DSP-Silverlake without bit 39
0206	Internal system error: Read response from DSP-Silverlake without bit126
0207	Invalid card number: Card number not belong to this CIF
2101	Invalid card number: Card not found
2102	Not enough balance
2103	Invalid customer account
2104	DSP-Silverlake system error
2199	Receive error response from DSP-Silverlake
0301	Internal system error: Cannot connect to VAM
3101	Invalid XML request: Invalid data XML (tc)
3102	Invalid XML request: Invalid data XML (userid)
3103	Invalid XML request: Invalid data XML (trace number)
3104	Invalid XML request: Invalid data XML (reference number)
3105	Invalid XML request: Invalid data XML (datetime)
3106	Invalid XML request: Invalid data XML (merchantid)
3107	Invalid XML request: Invalid data XML (bankid)
3108	Invalid XML request: Invalid data XML (item detail)
3109	Invalid XML request: Invalid data XML (amount)
3110	Invalid XML request: Invalid data XML (challenge)
3111	Invalid XML request: Invalid data XML (authentication)
3112	Invalid XML request: Invalid data XML (signature)
3113	Invalid XML request: Invalid data XML (aggregator)
3114	Invalid XML request: Error parse XML
3115	Invalid XML request: XML data is null
3116	Invalid XML request: Unmatched signature request
3117	Invalid XML request: Cannot find Aggregator
3118	User already registered: Duplicate UserID
3119	Customer account not found: Cannot find customer account
3120	Not registered UserID
3121	Daily transaction limit is reached
3122	Maximum transaction limit is reached
3123	Transaction payment rejected: Invalid limit configuration
3124	Transaction payment rejected: Cannot find Merchant ID
3125	Transaction payment rejected: Inactive merchant
3126	Transaction payment rejected: Cannot find Bank Commission
3127	Transaction payment rejected: Cannot find Bank Commission Tearing
3128	Transaction payment rejected: Cannot find Aggregator Commission
3129	Transaction payment rejected: Cannot find Aggregator Commission T earing
3130	Transaction payment rejected: Duplicate Transaction request
3131	Reversal rejected: Cannot find original data for reversal
3132	Reversal rejected: Cannot find merchant account for reversal
3133	Registration failed: Failed add customer channel
3134	Unregistered failed: Failed remove customer channel
3135	Merchant registration failed: Duplicate Merchant
3201	Error init database
3202	Error write to database
4000	No connection to Aggregator
9000	Other error
9013	Unable to send request to bank
DOKU Wallet Response Code
Response Code	Description
0E01	Failed Get Merchant
0E02	Master Merchant Inactive
0E03	Invalid Words from Merchant
0E04	Invalid Merchant
0E05	Failed to Process Payment
0E06	Payment Method not Defined
0E07	Failed to Execute Pre Auth Plugins
0E08	Failed to Execute Post Auth Plugins
0E09	Invalid Pay ID
0E10	Error Pay ID
0E11	Failed to Execute Pre Trans Pre Trans MIP Plugins
0E12	Verify Response STOP From Merchant
0E13	Failed Verify to Merchant
0E14	Failed Send Payment Cash Wallet
0E15	Notify Response STOP From Merchant
0E16	Failed Notify to Merchant
0E18	Failed to Execute Post Trans MIP Plugins
0E19	Not Enough Cash Balance and Don't Have Credit Card
0E20	Spender Does Not Have Link to Credit Card
0E21	Error Check 3D Secure Credit Card
0E22	PIN/OTP Is Not Valid
0E23	Please Input CVV2
0E24	Invalid Session
0E25	Failed to Send Link Authentication to Card Holder
0E26	Insufficient Params
0E27	Failed to Execute Pre Trans CIP Plugins
0E28	Failed to Execute Post Trans CIP Plugins
0E29	Failed to Send Payment MIP Credit Card
0E30	You Do Not Have PIN
0E31	Duplicate Invoice No
0E32	URL Not Found
0E33	Customer Not Found
0E34	Void Process Failed
0E35	Failed Send ONE TIME PIN to your email
0E36	Failed Send Link to create PIN to your email
0E37	This Spender Cannot Transact in This Merchant
0E38	You Have Reach Your DOKU ID Transaction Limit
0E39	Process MIP Transaction Failed
0E99	Error System
BRI e-Pay Response Code
Response Code	Description
0001	Failed to notify Merchant
0020	General error
0021	Wrong password
0022	Wrong paycode
0023	Transaction cancelled
0024	User ID is being used
0025	User has not registered M-Token
0026	Timeout
0027	Invalid parameter
0028	User ID is being blocked
0029	User ID not found
0030	Transaction limit exceeded
0031	User not found
0032	Failed to show BRI pop up (deprecated)
0033	Failed to show BRI pop up (deprecated)
0048	Failed to redirect to BRI e-Pay
0066	Page already redirected back to DOKU but not getting any payment result from BRI (not getting notify and not getting response from 3 times check status)
Alfa / Indomaret / Permata / Mandiri / Sinarmas VA Response Code
Response Code	Description
0001	Decline (internal error)
0013	Invalid amount
0014	Bill not found
0066	Decline
0088	Bill already paid
Payment Channel Code
Code	Description
02	Mandiri ClickPay
03	KlikBCA
04	DOKU Wallet
06	BRI e-Pay
15	Credit Card
16	Credit Card Tokenization
17	Recurring Payment
18	BCA KlikPay
19	CIMB Clicks
22	Sinarmas VA
23	MOTO
25	Muamalat Internet Banking
26	Danamon Internet Banking
28	Permata Internet Banking
29	BCA VA
31	Indomaret
32	CIMB VA
33	Danamon VA
34	BRI VA
35	Alfa VA
36	Permata VA
37	Kredivo
38	BNI VA
39	Linepay ECash
41	Mandiri VA
42	QNB VA
43	BTN VA
44	Maybank VA
45	BNI Yap!
47	Arta Jasa VA
Test Data & Simulator
Credit or Debit Card
Please use Expiry and CVV below:

Exp	CVV
02 / 22	123
MASTERCARD
Scenario	Card number
3DS Success	5481 1611 1111 1081
3DS Rejected by DOKU	5110 1111 1111 1119
3DS Rejected by Bank	5210 1111 1111 1118
Non 3DS Success	5211 1111 1111 1117
Non 3DS Rejected by DOKU	5111 1111 1111 1118
Non 3DS Rejected by Bank	5410 1111 1111 1116
VISA
Scenario	Card Number
3DS Success	4011 1111 1111 1111
3DS Rejected by DOKU	4111 1111 1111 1112
3DS Rejected by Bank	4211 1111 1111 1110
Non 3DS Success	4811 1111 1111 1114
Non 3DS Rejected by DOKU	4911 1111 1111 1113
Non 3DS Rejected by Bank	4411 1111 1111 1118
Bank Specific Card
Mandiri

Scenario	Visa	Mastercard
3DS Success	4617 0069 5974 6656	5573 3810 7219 6900
Non 3DS Success	4617 0017 4194 2101	5573 3819 9982 5417
BNI

Scenario	Visa	Mastercard
3DS Success	4105 0586 8948 1467	5264 2210 3887 4659
Non 3DS Success	4105 0525 4151 2148	5264 2249 7176 1016
CIMB Niaga

Scenario	Visa	Mastercard
3DS Success	4599 2078 8712	2414 5481 1698 1883 2479
Non 3DS Success	4599 2039 9705 2898	5481 1671 2103 2563
BCA

Scenario	Visa	Mastercard
3DS Success	4773 7760 5705 1650	5229 9031 3685 3172
Non 3DS Success	4773 7738 1098 1190	5229 9073 6430 3610
BRI

Scenario	Visa	Mastercard
3DS Success	4365 0263 3573 7199	5520 0298 7089 9100
Non 3DS Success	4365 0278 6723 2690	5520 0254 8646 8439
Maybank

Scenario	Visa	Mastercard
3DS Success	4055 7720 2603 6004	5520 0867 5210 2334
Non 3DS Success	4055 7713 3514 4012	5520 0867 7490 8452
Virtual Account Simulator
Payment Channel	Payment Channel Code	Simulator URL
Permata VA	36	https://staging.doku.com/VASimulator/PermataAction_show.doku
BCA VA	29	https://staging.doku.com/VASimulator/BCAAction_show.doku
Mandiri VA	41	https://staging.doku.com/VASimulator/MandiriAction_show.doku
Sinarmas	22	https://staging.doku.com/VASimulator/SinarmasAction_show.doku
CIMB VA	32	https://staging.doku.com/VASimulator/CimbAction_show.doku
Danamon VA	33	https://staging.doku.com/VASimulator/DanamonAction_show.doku
BRI VA	34	https://staging.doku.com/VASimulator/BriAction_show.doku
BNI VA	40	https://staging.doku.com/VASimulator/BNIAction_show.doku
BNI Bill payment		https://staging.doku.com/VASimulator/BniBPAction_show.doku
Alfa	35	https://staging.doku.com/VASimulator/AlfaAction_show.doku
Indomaret	31	https://staging.doku.com/VASimulator/IndomartAction_show.doku
Maybank	44	https://staging.doku.com/VASimulator/GeneralAction_show.doku
Internet Banking Simulator
Payment Channel	Username / Card Number	Token / Password
Mandiri Clickpay	4111111111111111	000000
PermataNet	admin	admin
KlikBCA	admin	123456
BRI e-pay	irfani	100291
CIMB Clicks	config per merchant by DOKU	config per merchant by DOKU
IB Muamalat	admin	admin
IB Danamon	admin	admin
DOKU Wallet Simulator
DOKU ID	Password	PIN
1909800024	dokutes123	1122
Going Live
(1) Make sure that you already test all scenarios required.

(2) Change your development shared key with production shared key. You can see your shared key in DOKU Merchant dashboard.

(3) For Merchant Hosted integrated, please change js and css URL to production URL below:

js :https://pay.doku.com/doku-js/assets/js/doku-1.2.js?version=1497508770
css : https://pay.doku.com/doku-js/assets/css/doku.css
(4) Change staging API URL (https://staging.doku.com/..) to production API URL (https://pay.doku.com/..).

Version
Document version 1.0
July 31, 2018

Initial document

javascriptphpxml