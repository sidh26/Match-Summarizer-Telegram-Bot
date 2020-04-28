import requests
from bottle import Bottle, response, request as bottle_request
import pandas as pd


class BotHandlerMixin:
    BOT_URL = None
    
    def get_chat_id(self, data):
        """
        Method to extract chat id from telegram request.
        """
        chat_id = data['message']['chat']['id']
        
        return chat_id
    
    def get_message(self, data):
        """
        Method to extract message id from telegram request.
        """
        message_text = data['message']['text']
        
        return message_text
    
    def send_message(self, prepared_data):
        """
        Prepared data should be json which includes at least `chat_id` and `text`
        """
        message_url = self.BOT_URL + 'sendMessage'
        requests.post(message_url, json=prepared_data)
    
    def send_image(self, imgdata):
        """
        Prepared data should be json which includes at least `chat_id` and `text`
        """
        message_url = self.BOT_URL + 'sendPhoto'
        requests.post(message_url, json=imgdata)


class TelegramBot(BotHandlerMixin, Bottle):
    BOT_URL = 'https://api.telegram.org/bot1223437002:AAGppaUdzRoMmpw1Z4wyN5xP_pP_TClxw08/'
    
    def __init__(self, *args, **kwargs):
        self.df = pd.read_csv("D:/Downloads/events.csv")
        self.commentary = self.df.groupby(['id_odsp'])['text'].apply(' '.join).reset_index()[:5009]
        self.pred = pd.read_csv("D:/Downloads/outcome_predictions.csv")[:5009]
        self.ginf = pd.read_csv("D:/Downloads/ginf.csv")[:5009]
        with open("D:/Downloads/result.txt", 'r', encoding='cp850') as f:
            temp = f.readlines()
        self.commentary['summary'] = temp
        super(TelegramBot, self).__init__()
        self.route('/', callback=self.post_handler, method="POST")
    
    def reply(self, message, data):
        """
        To handle replies
        """
        if message.lower() == 'show matches':
            temp = ''
            for index, row in self.ginf[['ht', 'at']][:25].iterrows():
                temp += row['ht'] + ' vs. ' + row['at'] + '\n'
            return temp.strip('\n')
        elif message.lower() == 'xg analysis':
            img2 = "https://drive.google.com/file/d/12P7zl-yK4Is9-DOvPJY9yMTSlHGvgpjV/view?usp=sharing"
            cap2 = 'Analysing Factors that impact the prediction of Expected Goal'
            imgdata2 = self.prepare_img_for_answer(data, img2, cap2)
            self.send_image(imgdata2)
            
            img1 = 'https://drive.google.com/file/d/12_8PpMB_C7jQS7UaKSrcXm7fJgndTKpW/view?usp=sharing'
            cap1 = 'Confusion Matrix of Ridge Classifier Model for Prediction of Expected Goal'
            imgdata1 = self.prepare_img_for_answer(data, img1, cap1)
            self.send_image(imgdata1)
            
            return 'Analysis of Expected Goals'
        else:
            # print outcome prediction
            t = message.split(' vs. ')
            matches = self.pred['Predicted Outcome'][(self.ginf['ht'] == t[0]) & (self.ginf['at'] == t[1])]
            final = 'There were ' + str(matches.shape[0]) + ' matches for which the Match Predictions are:\n'
            for row in matches:
                final += row + '\n'
            
            # print summary
            summ = self.commentary['summary'][(self.ginf['ht'] == t[0]) & (self.ginf['at'] == t[1])]
            final += '\nThe Match Summaries are:\n'
            for row in summ:
                final += row + '\n'
            return final.strip('\n')
    
    def prepare_data_for_answer(self, data):
        message = self.get_message(data)
        answer = self.reply(message, data)
        chat_id = self.get_chat_id(data)
        json_data = {
            "chat_id": chat_id,
            "text": answer,
        }
        
        return json_data
    
    def prepare_img_for_answer(self, data, img, cap):
        
        chat_id = self.get_chat_id(data)
        json_data = {
            "chat_id": chat_id,
            "photo": img,
            "caption": cap,
        }
        
        return json_data
    
    def post_handler(self):
        data = bottle_request.json
        answer_data = self.prepare_data_for_answer(data)
        self.send_message(answer_data)
        
        return response


if __name__ == '__main__':
    app = TelegramBot()
    app.run(host='localhost', port=8080)
