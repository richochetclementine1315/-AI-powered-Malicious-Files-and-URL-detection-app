from flask import Flask,render_template,request #Flask for creating the application, render_template fro setting up communication between BE & FE, request for requesting
import google.generativeai as genai #using googles generative AI for evaluating the files based on prompts.
import os
import PyPDF2 #used for text extraction from .txt and pdf file
from dotenv import load_dotenv#for taking data from .env files



#Initialize Flask app
app=Flask(__name__)

#SetUp The Google API Key
load_dotenv()
api_key=os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY is noyt set in .env file")
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

#Initialize the Gemini Model
model=genai.GenerativeModel("gemini-1.5-flash")
#function that takes the text and predicts fake or real....here in this function we give the prompt to the genai model
def predict_fake_or_real_file_context(text):
    # putting the prompt.....
    prompt=  f"""
    You are an expert in identifying scam messages in text, email etc. Analyze the given text and classify it as:

    - **Real/Legitimate** (Authentic, safe message)
    - **Scam/Fake** (Phishing, fraud, or suspicious message)

    **for the following Text:**
    {text}

    **Return a clear message indicating whether this content is real or a scam. 
    If it is a scam, mention why it seems fraudulent. If it is real, state that it is legitimate.**

    **Only return the classification message and nothing else.**
    Note: Don't return empty or null, you only need to return message for the input text
    """
    #recording response 
    response = model.generate_content(prompt)
    #taking out the message
    return response.text.strip() 


#this is the function where we put prompts for the URL detction part
def url_detection(url):
    
    promt=   f"""
    You are an advanced AI model specializing in URL security classification. Analyze the given URL and classify it as one of the following categories:
    1. Benign**: Safe, trusted, and non-malicious websites such as google.com, wikipedia.org, amazon.com.
    2. Phishing**: Fraudulent websites designed to steal personal information. Indicators include misspelled domains (e.g., paypa1.com instead of paypal.com), unusual subdomains, and misleading content.
    3. Malware**: URLs that distribute viruses, ransomware, or malicious software. Often includes automatic downloads or redirects to infected pages.
    4. Defacement**: Hacked or defaced websites that display unauthorized content, usually altered by attackers.

    **Example URLs and Classifications:**
    - **Benign**: "https://www.microsoft.com/"
    - **Phishing**: "http://secure-login.paypa1.com/"
    - **Malware**: "http://free-download-software.xyz/"
    - **Defacement**: "http://hacked-website.com/"

    **Input URL:** {url}

    **Output Format:**  
    - Return only a string class name
    - Example output for a phishing site:  

    Analyze the URL and return the correct classification (Only name in lowercase such as benign etc.
    Note: Don't return empty or null, at any cost return the corrected class
    """
    #recording response
    response=model.generate_content(promt)
    return response.text if response else "Detection Failed :("



#routes
@app.route("/")
def index():
    return render_template("index.html")

#WORKING FOR THE >PDF AND >TXT SECTION
#Now making the API Endpoints
@app.route("/scam/",methods=['GET','POST'])
def detect_scam():
    #checking if the file is uploaded or not.If not then a message will be shown
    if 'file' not in request.files:
        return render_template('index.html', message="No file Uploaded!")
    #if uploaded, we fetch the file by request.(means basically it will accept the file)
    file=request.files['file']


    #for extractting the text from pdf or .txt file so that it can be checked whether fraud or not :)
    extracted_text=""
    #checking whether its a pdf file or .txt file
    if file.filename.endswith(".pdf"):
      #extracting texts from(file) by PdfReader function in PyPDF2
      pdf_reader= PyPDF2.PdfReader(file)
      extracted_text=" ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
      #if uploaded .txt, then read the file and then decode it
    elif file.filename.endswith(".txt"):
        extracted_text=file.read().decode("utf-8")
    else:
        return render_template('index.html',message="Files is empty or text could not be extracted")  

    #calling the function fake or real file context
    # basically the extracted text will be evaluated according to the prompt specified in this function

    Message= predict_fake_or_real_file_context((extracted_text))


    # this will actually pront the message afte evaluation. That teh user can see.
    return render_template('index.html',message=Message)


# NOW FOR THE URL PART.....
# API endpoint making for url part
@app.route("/predict", methods=['GET','POST'])
def url_predict():
    if request.method=='POST':
        # taking the url and if any spaces are there then removing that using the strip() function
        url=request.form.get("url",'').strip()
        #if urls star with https:// and http:// then only we'll check else pass and produce a message as invalid
        if not url.startswith(('https://','http://')):
            return render_template('index.html',message="INVALID URL !!")
        #getting the respose given by the prompt and then further passing it to the index.html to show to the users
        classification=url_detection(url)
        return render_template("index.html", input_url=url, predicted_class=classification)


#python main
if __name__=="__main__":
    app.run(debug=True)