from kivymd.app import MDApp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

from overall import Website as web
from profile import Profile as prof
import numpy as np

# import spotipy as spot
# import sys

Builder.load_file('interface.kv')

class LoginPage(Screen):
    pass

class GenrePage(Screen):
    pass

class ArtistPage(Screen):
    pass

class SongPage(Screen):
    pass

class PlaylistPage(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class MainWindow(StackLayout):
    
    # https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db
    # CSV File from link above
    web_data = web('SpotifyFeatures.csv')
    df = web_data.get_data()
    user = prof(df)
    num_songs_asked = 0
    songs_to_ask = []

    path_to_LP = None
    path_to_GP = None
    path_to_AP = None
    path_to_SP = None

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.path_to_LP = self.ids.loginPage.ids 
        self.path_to_GP = self.ids.genrePage.ids
        self.path_to_AP = self.ids.artistPage.ids
        self.path_to_SP = self.ids.songPage.ids

    """
    The following functions are used for storing user entered data from
    the Login Page:
        set_username
        set_spotlink
    """
    def set_username(self):
        self.user.set_name(self.path_to_LP.username.text)
        # print(self.user.get_name())
    
    def set_spotlink(self):
        self.user.set_spotlink(self.path_to_LP.link.text)
        # print(self.user.get_spotlink())
    
    """
    The following functions are used for implementing buttons that represent
    each genre on the Genre Page, and they also store user data:
        edit_genre_list
        genreButtons
    """
    def edit_genre_list(self, instance):
        if instance.background_color == [1.0, 0.0, 0.0, 1.0]:
            instance.background_color = 'green'
            self.user.add_top_genre(instance.text)
        else:
            instance.background_color = 'red'
            self.user.delete_top_genre(instance.text)
    
    def genreButtons(self):
        genres = (self.df.genre).unique()
        for genre in genres:
            cur_button = Button(text=genre, 
                                font_size=25,
                                size_hint=(.2, .147), 
                                background_color='red')
            cur_button.bind(on_press=self.edit_genre_list)
            self.path_to_GP.stack.add_widget(cur_button)

    """
    The following functions are used for implementing buttons that represent
    each artist the user searches for on the Artist Page, and they also store 
    user data:
        implement_tops_songs
        edit_artist_list
        artist_search
    """
    def implement_tops_songs(self, artist):
        songs = self.web_data.get_artist_top_songs(artist)
        layout = GridLayout(cols=1, rows=10)
        rank = 1
        for song in songs:
            if len(song) > 30: 
                song = f'{song[:30]}...' 
            txt = f'{rank}. {song}'
            cur_button = Button(text=txt, 
                                font_size=25,
                                size_hint=(.2, .05), 
                                background_color='blue')
            # cur_button.bind()
            # in the future we would bind a function that plays a 30 second snippet of the song
            layout.add_widget(cur_button)
            rank += 1
        self.path_to_AP.topSongs.add_widget(layout)

    def edit_artist_list(self, instance):
        self.path_to_AP.topSongs.clear_widgets()
        if instance.background_color == [1.0, 0.0, 0.0, 1.0]:
            instance.background_color = 'green'
            self.user.add_top_artist(instance.text)
            self.implement_tops_songs(instance.text)
        else:
            instance.background_color = 'red'
            self.user.delete_top_artist(instance.text)

    def artist_search(self):
        self.path_to_AP.searchResults.clear_widgets()
        self.path_to_AP.topSongs.clear_widgets()
        entry = self.path_to_AP.searchEntry.text
        if len(entry) == 0: return
        search = self.user.searching(entry)
        layout = GridLayout(cols=1, rows=10)
        for result in search:
            tops = self.user.get_top_artists()
            color = 'red' if tops.count(result) == 0 else 'green'
            cur_button = Button(text=result, 
                                font_size=25,
                                size_hint=(.2, .05), 
                                padding=(10,30),
                                background_color=color)
            cur_button.bind(on_press=self.edit_artist_list)
            layout.add_widget(cur_button)
        self.path_to_AP.searchResults.add_widget(layout)

    """
    SongPage functions:
        set_songs_to_ask
        get_song
        initialize
        make_decision
    """
    
    def set_songs_to_ask(self):
        songs = []
        fav_genres = self.user.get_top_genres()
        df_and_matrix = self.web_data.make_matrix_by_genres('genre', fav_genres)
        og_df = df_and_matrix[0]
        og_df_idxs = list(og_df.index)
        cur_df = og_df.reset_index(drop=True)
        matrix = df_and_matrix[1]
        for artist in self.user.get_top_artists():
            indexes = (cur_df.query('artist_name == @artist').index).to_numpy()
            for idx in indexes:
                similiar_songs = list(enumerate(matrix[idx]))
                filter_sim_songs = np.array([x for x in similiar_songs if x[1] > 0.73])
                for song in filter_sim_songs:
                    songs.append(og_df_idxs[int(song[0])])
        self.songs_to_ask = songs

    def get_song(self, index):
        name = self.df.iloc[index][self.df.columns[2]]
        artist = self.df.iloc[index][self.df.columns[1]]
        return f'{name} by {artist}' 

    def initialize(self):
        songs = self.songs_to_ask
        idx = self.num_songs_asked
        self.path_to_SP.song.name = str(idx)
        self.path_to_SP.song.text = self.get_song(songs[idx])
        self.num_songs_asked += 1
    
    def make_decision(self, isLike):
        idx = int(self.path_to_SP.song.name)
        if isLike:
            self.user.add_liked_song(idx)
        else:
            self.user.add_disliked_song(idx)
        self.initialize()

    pass

class myApp(MDApp):

    def build(self):
        return MainWindow()


if __name__ == "__main__":
    st = myApp()
    st.run()