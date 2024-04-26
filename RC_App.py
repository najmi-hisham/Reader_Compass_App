import streamlit as st
import os,openai 
from dotenv import load_dotenv
import re
import pandas as pd
import datetime

load_dotenv()

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "book" not in st.session_state:
    st.session_state.book = []

def extract_info(text):
    titles_descriptions = []
    matches = re.findall(r"^(\d+\. )(.+?)(?: by (.+?))? \[(.+?)\] - (.*)$", text, flags=re.MULTILINE)

    for match in matches:
        title, author, genre, description = match[1], match[2], match[3], match[4]
        # Extract genre information within brackets
        current_time = datetime.datetime.now().strftime("%H:%M:%S")  # Get current time
        titles_descriptions.append({
        "TITLE": title,
        "AUTHOR": author if author else "NA",
        "GENRE": genre,
        "DESCRIPTION": description,
        "TIME ACCESS": current_time  # Add current time to the dictionary
        })

    return titles_descriptions


def get_assistant_response(user_input, message_list):
    message_list.append({"role": "user", "content": user_input})
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=message_list,
        max_tokens=1000,  # Adjust the maximum number of tokens based on your needs
    )

    assistant_output = response.choices[0].message.content
    message_list.append({"role": "assistant", "content": assistant_output})

    return assistant_output, message_list

def update_book_list_df():
    st.session_state.update_df = True 

def page_home():
    assistant_output = ""  # Initialize assistant_output
    st.title("READER COMPASS 📖")
    

    message_list = [{"role": "system", "content": "You are a helpful and friendly bot that recommended people with book that relevant to their interest. You also give them advice about books after recommending it"}]

    with st.sidebar:
        book_genres = (
            "Fiction",
            "Non-Fiction",
            "Mystery/Thriller",
            "Science Fiction (Sci-Fi)",
            "Fantasy",
            "Romance",
            "Horror",
            "Historical Fiction",
            "Children's and Young Adult",
            "Comics and Graphic Novels",
            "Science and Nature",
            "Others"
            )
        
        Top_n = st.number_input("Enter the number of recommendations:", min_value=0, max_value=10, step=1)
        prompt = f"Please give me recommendation of top {Top_n} book that relevant to my interest below:\n"

        book_genres = ["Fiction", "Non-fiction", "Mystery", "Thriller", "Fantasy", "Science Fiction", "Others"]

        selected_genre = st.multiselect("Which is your genre choices:", options=book_genres)

        if "Others" in selected_genre:
            num_custom_genres = st.number_input("How many custom genres do you want to add?", min_value=0, step=1)
            
            custom_genres = []
            for i in range(num_custom_genres):
                custom_genre = st.text_input(f"Custom Genre {i+1}:")
                if custom_genre:
                    custom_genres.append(custom_genre)
                    
            selected_genre.extend(custom_genres)
            selected_genre = [genre for genre in selected_genre if genre != "Others"]
                
        prompt += f"Genre: {selected_genre}.\n\n"


        selected_age = st.selectbox("Please choose your age:", options=("7-12", "13-24", "24-above"))
        prompt += f"My age is around {selected_age}. If you consider me as underage please restrict book that only for underage.\n\n"

        author_have = st.checkbox("Do you have any favourite author to add?")
        if author_have:
            author = st.text_input("Please input the author:", key="author_input")
            prompt += f"Author: {author}\nIf possible, please recommend the book from {author}. If not you please prioritize the genre\n\n"
        else:
            prompt += f"Author: You can choose any author.\n\n"

        fav_book = st.checkbox("Can give me one of your favourite book. Ignore if you not intend to input")
        if fav_book:
            fav = st.text_input("Please input the book title:", key="book_title_input")
            prompt += f"Previous favourite book: {fav}.\n\nMy previous reading experiences, I love to read the book titled {fav}. If you don't know about the book, you can ignore it.\n\n"
        else:
            prompt += ""

        keyword = st.checkbox("Can give me any keyword like magic, robot etc. Ignore if you not intend to input")
        if keyword:
            key = st.text_input("Please input the keyword:", key="keyword_input")
            prompt += f"Keyword: {key}.\n\n"
        else:
            prompt += ""

        expect = st.text_input("What is your expectation for the book")
        prompt+= f"Expectation of the books: {expect}.\n\n"

        if st.session_state.get("book"):
            prompt+=f"Please exclude books below:\n"
            existing_book_titles = [book["TITLE"] for book in st.session_state.book if book]  # Access titles only if book exists in the list
            for title in existing_book_titles:
                prompt += f"- {title}\n"
    # Display book titles or use the data
        else:
            prompt+=""

        prompt+= f"""Please give me in point form with short description. Like below:\n1. [title] [major genre (max 3)] - [description] \n Noted: Please follow the format above
        For example below is the true format:
        1. "Harry Potter and the Sorcerer's Stone" by J.K. Rowling [Fantasy, Magic, Adventure] - This classic tale follows young Harry Potter as he discovers his magical abilities and attends Hogwarts School of Witchcraft and Wizardry. It's a great choice for inspiring creativity and imagination.
        
        Example below is the false format:
        1. "Hello Ruby: Journey Inside the Computer" by Linda Liukas - deep learning, children's, technology
                - This interactive book introduces young readers to the world of technology, including the basics of deep learning, through a playful story and engaging activities.
        2. "Gone Girl" by Gillian Flynn (Thriller, Mystery) - This gripping psychological thriller follows the sudden disappearance of Amy Dunne and the subsequent investigation into her vanishing. Told from alternating perspectives, this novel is filled with twists and turns that will keep you guessing until the very end. The complex characters and layered storytelling make "Gone Girl" a compelling read for thriller enthusiasts.
"""
        
        #st.write(prompt)
        get_list = st.button("generate")

    if get_list and Top_n and selected_genre:
        assistant_output, message_list = get_assistant_response(prompt, message_list)
        st.write(assistant_output)
        new_books = extract_info(assistant_output)
        #print(f"Assistant Output: {assistant_output}")
        #print(f"Extracted Book Info: {new_books}")
        st.session_state.book += new_books  # Append new data to existing list
        update_book_list_df()

    else:
        st.write("Please input number of list,genre,age,expectations and press generate")
    
    #user_input = st.chat_input("Anything:")

def handle_delete(idx):
    del st.session_state['book'][idx]


def display_page():
    st.title('Book List ✅')

    check = st.checkbox("Open table")

    # Check if update flag is set and book data is not empty
    if check:
        df = pd.DataFrame(st.session_state.book)
        st.table(df)
        st.session_state.update_df = False  # Reset flag after update

    if st.checkbox("Do you want to remove certain books?"):
        for idx, item in enumerate(st.session_state['book']):
            st.button(f"Delete {item['TITLE']}", key=idx, on_click=handle_delete, args=(idx,))

def instruction_page():
    col1, col2, col3 = st.columns(3)

    with col2:
        st.title("About us")

    text = """"Our Mission:  At Reader Compass, we're passionate about igniting a love of reading and empowering every reader to find their perfect match.

The Power of AI:  We leverage cutting-edge Artificial Intelligence to personalize book recommendations, taking the guesswork out of your literary journey.

Who We Serve:  Reader Compass caters to readers of all backgrounds and interests. Whether you're a seasoned bibliophile or a curious student, we help you discover books that fuel your imagination and expand your horizons.

Our Promise:  We believe that reading should be an enriching and enjoyable experience.  With Reader Compass, you can say goodbye to buyer's remorse and wasted time browsing.

Join the Journey:  Let us be your guide on the path to literary discovery.  Download Reader Compass today and unlock a world of personalized book recommendations!"""

    st.write(text)

def main():
    st.sidebar.title('Navigation')
    page = st.sidebar.radio('Go to', ['Home', 'My Book List',"About Us"])

    if page == 'Home':
        page_home()
    elif page == 'My Book List':
        display_page()
    elif page == "About Us":
        instruction_page()

if __name__ == '__main__':
    main()