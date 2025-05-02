from openai import OpenAI

client = OpenAI(api_key="sk-mah6FUel7jrB3lNj8c3cnqUGeKy1ovL5DAD1GFge92C7Fe864c8646B1B9DaB6C20a10A896", 
                base_url="http://14.103.16.83:25822/v1")

messages = [
  {
    "role": "system",
    "content": "Imagine you are a robot browsing the web, just like humans. Now you need to complete a task. In each iteration, you will receive an Observation that includes a screenshot of a webpage and some texts. This screenshot will feature Numerical Labels placed in the TOP LEFT corner of each Web Element.\nCarefully analyze the visual information to identify the Numerical Label corresponding to the Web Element that requires interaction, then follow the guidelines and choose one of the following actions:\n1. Click a Web Element.\n2. Delete existing content in a textbox and then type content. \n3. Scroll up or down. Multiple scrolls are allowed to browse the webpage. Pay attention!! The default scroll is the whole window. If the scroll widget is located in a certain area of the webpage, then you have to specify a Web Element in that area. I would hover the mouse there and then scroll.\n4. Wait. Typically used to wait for unfinished webpage processes, with a duration of 5 seconds.\n5. Go back, returning to the previous webpage.\n6. Google, directly jump to the Google search page. When you can't find information in some websites, try starting over with Google.\n7. Answer. This action should only be chosen when all questions in the task have been solved.\n\nCorrespondingly, Action should STRICTLY follow the format:\n- Click [Numerical_Label]\n- Type [Numerical_Label]; [Content]\n- Scroll [Numerical_Label or WINDOW]; [up or down]\n- Wait\n- GoBack\n- Google\n- ANSWER; [content]\n\nKey Guidelines You MUST follow:\n* Action guidelines *\n1) To input text, NO need to click textbox first, directly type content. After typing, the system automatically hits `ENTER` key. Sometimes you should click the search button to apply search filters. Try to use simple language when searching.  \n2) You must Distinguish between textbox and search button, don't type content into the button! If no textbox is found, you may need to click the search button first before the textbox is displayed. \n3) Execute only one action per iteration. \n4) STRICTLY Avoid repeating the same action if the webpage remains unchanged. You may have selected the wrong web element or numerical label. Continuous use of the Wait is also NOT allowed.\n5) When a complex Task involves multiple questions or steps, select \"ANSWER\" only at the very end, after addressing all of these questions (steps). Flexibly combine your own abilities with the information in the web page. Double check the formatting requirements in the task when ANSWER. \n* Web Browsing Guidelines *\n1) Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages. Pay attention to Key Web Elements like search textbox and menu.\n2) Vsit video websites like YouTube is allowed BUT you can't play videos. Clicking to download PDF is allowed and will be analyzed by the Assistant API.\n3) Focus on the numerical labels in the TOP LEFT corner of each rectangle (element). Ensure you don't mix them up with other numbers (e.g. Calendar) on the page.\n4) Focus on the date in task, you must look for results that match the date. It may be necessary to find the correct year, month and day at calendar.\n5) Pay attention to the filter and sort functions on the page, which, combined with scroll, can help you solve conditions like 'highest', 'cheapest', 'lowest', 'earliest', etc. Try your best to find the answer that best fits the task.\n\nYour reply should strictly follow the format:\nThought: {Your brief thoughts (briefly summarize the info that will help ANSWER)}\nAction: {One Action format you choose}\n\nThen the User will provide:\nObservation: {A labeled screenshot Given by User}"
  },
  {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "Hello!"
      }
    ]
  }
]

openai_response = client.chat.completions.create(
                    model="/mnt/cache/sharemath/models/Qwen/Qwen2.5-VL-7B-Instruct", messages=messages, max_tokens=1000, seed=42
                )

print(openai_response.choices[0].message.content)