from fastapi import FastAPI, Depends, HTTPException, status, Header, Form, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import session
from . import crud, schemas, hashing, token
from .database import session_local, engine, Base
app = FastAPI(title="HIMS' Stackoverflow")

Base.metadata.create_all(bind=engine)

def get_DB():
    db = session_local()
    try:
        yield db
    finally:
        db.close()




@app.post("/login", tags=["admin", "User"])
async def login(db: session = Depends(get_DB), email : EmailStr = Form(...), password : str = Form(...), isAdmin : bool = Form(...)):
    if isAdmin:
        admin_db = crud.get_admin(db, email)
        if not admin_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        if not hashing.verify_password(password, admin_db.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        data = {
            "admin_id" : admin_db.id
        }
        jwt_token = token.encode_token(data)
        return jwt_token
    else:
        User_db = crud.get_User(db, email)
        if not User_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        if not hashing.verify_password(password, User_db.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Password or email")
        data = {
            "User_id" : User_db.id
        }
        jwt_token = token.encode_token(data)
        return jwt_token

@app.post("/create_admin", response_model=schemas.AdminOut, tags=["admin"])
async def create_admin(admin : schemas.AdminIn, db : session = Depends(get_DB)):
    admin_db = crud.get_admin(db,admin.email)
    if admin_db:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_admin(db, admin)


@app.put("/update_admin_email", tags=["admin"])
async def update_admin_email(db : session = Depends(get_DB), new_email : EmailStr = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_admin_email(db, token_data["admin_id"], new_email)
    return {
        "message" : "email updated successfuly"
    }
@app.put("/update_admin_password", tags=["admin"])
async def update_admin_email(db : session = Depends(get_DB), new_password : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_admin_password(db, token_data["admin_id"], new_password)
    return {
        "message" : "password updated successfuly"
    }

@app.delete("/delete_admin", tags=["admin"])
async def delete_admin(db : session = Depends(get_DB), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    if "User_id" in token_data.keys():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorised for this route")
    admin_id = token_data["admin_id"]
    crud.delete_admin(db, admin_id)

@app.post("/create_User", response_model=schemas.AdminOut, tags=["User"])
async def create_User(User : schemas.UserIn, db : session = Depends(get_DB)):
    User_db = crud.get_User(db,User.email)
    if User_db:
        raise HTTPException(status_code=400, detail="User already exists")
    if crud.get_admin(db, User.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin can not be a User")
    return crud.create_User(db, User)

@app.put("/update_User_email", tags=["User"])
async def update_User_Email(db : session = Depends(get_DB), new_email : EmailStr = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_User_email(db, token_data["User_id"], new_email)
    return {
        "message" : "email updated successfuly"
    }

@app.put("/update_User_password", tags=["User"])
async def update_User_password(db : session = Depends(get_DB), new_password : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_User_password(db, token_data["User_id"], new_password)
    return {
        "message" : "password updated successfuly"
    }
@app.put("/update_User_name", tags=["User"])
async def update_User_name(db : session = Depends(get_DB), new_name : str = Form(...), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    crud.update_User_name(db, token_data["User_id"], new_name)
    return {
        "message" : "name updated successfuly"
    }


@app.delete("/delete_User", tags=["User"])
async def delete_User(db : session = Depends(get_DB), Token : str = Header(...)):
    token_data = token.decode_token(Token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid token")
    User_id = token_data["User_id"]
    crud.delete_User(db, User_id)






@app.post("/create_question", tags=["Question"])
async def create_question(question : schemas.QuestionIn, db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    crud.create_question(db, user_id, question)
    return {
        "message" : "success"
    }


@app.post("/create_answer", tags=["Answer"])
async def create_answer(answer : schemas.AnswerIn, db : session = Depends(get_DB), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    crud.create_answer(db, user_id, answer)
    return {
        "message" : "success"
    }

@app.get("/get_question_by_title", tags = ["Question"], response_model=list[schemas.QuestionOut])
async def get_question_by_title(title : str, db : session = Depends(get_DB)):
    questions = crud.get_questions_by_title(db, title)
    return questions

@app.get("/get_questions_by_tags", tags=["Question"], response_model=list[schemas.QuestionOut])
async def get_question_by_tags(tags : list[str] = Query(...), db : session = Depends(get_DB)):
    questions = crud.get_question_by_tags(db, tags)
    return questions


@app.put("/edit_question", tags=["Question"])
async def edit_question(question : schemas.QuestionIn, db : session = Depends(get_DB), ques_id : int = Query(...), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    crud.edit_question(db, user_id, ques_id, question)
    return {
        "message" : "question edited successfuly"
    }

@app.delete("/delete_question", tags=["Question"])
async def delete_question(db : session = Depends(get_DB), ques_id : int = Query(...), Token : str = Header(...)):
    data = token.decode_token(Token)
    user_id = data["User_id"]
    crud.delete_question(db, user_id, ques_id)
    return {
        "message" : "question deleted successfuly"
    }

@app.get("/get_answers_by_question_id", tags=["Answer"], response_model=list[schemas.AnswerOut])
async def get_answers_by_Question_id(que_id : int = Query(...), db : session = Depends(get_DB)):
    return crud.get_ans_by_que_id(db, que_id)


