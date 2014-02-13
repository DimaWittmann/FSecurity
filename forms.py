from wtforms import Form,  TextField, PasswordField, TextAreaField, validators

class NewFileForm(Form):
    title = TextField("Name", [validators.required("Please, enter title")])

    content = TextAreaField("Content", [validators.required("Please, enter content")])

class SignInForm(Form):
    nickname= TextField("Name", [validators.required("Please, enter name")]) 
    
    password = PasswordField("Password", [validators.required("Please, enter pass")]) 
   
   
class RegistrationForm(Form):
    nickname = TextField("Login", [validators.required("Please, enter nickname"), ])


    password = PasswordField("Password", [validators.Required("Please, enter password")])

    confirm = PasswordField("Confirm",  [validators.EqualTo("password", message="Passwords do not match")])


