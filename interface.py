from kivymd.app import MDApp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.clock import Clock
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
    df['Review'] = None
    user = prof(df)
    num_songs_asked = 0
    songs_to_ask = []

    path_to_LP = None
    path_to_GP = None
    path_to_AP = None
    path_to_SP = None
    path_to_PP = None

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.path_to_LP = self.ids.loginPage.ids 
        self.path_to_GP = self.ids.genrePage.ids
        self.path_to_AP = self.ids.artistPage.ids
        self.path_to_SP = self.ids.songPage.ids
        self.path_to_PP = self.ids.playlistPage.ids

    """
    Login Page Functions:
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
    Genre Page Functions:
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
    Artist Page Functions:
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
                                background_color='blue')
            # cur_button.bind()
            # in the future we would bind a function that plays a 30 second snippet of the song
            layout.add_widget(cur_button)
            rank += 1
        self.path_to_AP.topSongs.add_widget(layout)

    def allowOrDisallow(self):
        if len(self.user.get_top_artists()) >= 5:
            self.ids.WM.current = 'Song Page'
        else:
            self.path_to_AP.nextPage.text = 'Select >=5'


    def edit_artist_list(self, instance):
        self.path_to_AP.topSongs.clear_widgets()
        numArtistsSelected = len(self.user.get_top_artists())
        if instance.background_color == [1.0, 0.0, 0.0, 1.0]:
            instance.background_color = 'green'
            numArtistsSelected += 1
            if numArtistsSelected < 5:
                moreArts = 5 - numArtistsSelected
                self.path_to_AP.leftToSelect.text = f'Select {moreArts} or more Artists'
            else:
                self.path_to_AP.nextPage.text = 'continue to next page'
                self.path_to_AP.leftToSelect.text = 'You May Continue or Select More'
            self.user.add_top_artist(instance.text)
            self.implement_tops_songs(instance.text)
        else:
            instance.background_color = 'red'
            numArtistsSelected -= 1
            if numArtistsSelected < 5:
                moreArts = 5 - numArtistsSelected
                self.path_to_AP.nextPage.text = 'Select >=5'
                self.path_to_AP.leftToSelect.text = f'Select {moreArts} or more Artists'
            else:
                self.path_to_AP.leftToSelect.text = 'You May Continue or Select More'
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
                                background_color=color)
            cur_button.bind(on_press=self.edit_artist_list)
            layout.add_widget(cur_button)
        self.path_to_AP.searchResults.add_widget(layout)

    """
    Song Page Functions:
        set_songs_to_ask
        get_song
        initialize
        make_decision
        resetSTA
    """

    # green most: rgba(13, 120, 15, 1)
    # red most: rgba(230, 33, 5, 1)
    def implement_ratings(self):
        layout = GridLayout(rows=1, cols=10)
        colors = ['red', 'orange', 'yellow', 'blue', 'green']
        for x in range(5):
            cur_button = Button(text=str(x+1),
                                font_size=50,
                                background_color=colors[x])
            cur_button.bind(on_press=self.make_decision)
            layout.add_widget(cur_button)
        self.path_to_SP.ratings.add_widget(layout)

    def set_songs_to_ask(self):
        songs = []
        fav_artists = self.user.get_top_artists()
        fav_genres = self.user.get_top_genres()
        df_and_matrix = self.web_data.make_matrix_by_genres(fav_artists, fav_genres)
        cur_df = df_and_matrix[0]
        matrix = df_and_matrix[1]
        self.user.set_df(cur_df)
        self.user.set_personal_matrix(matrix)
        idxs_fav_art_songs = ((cur_df[cur_df['artist_name'].isin(fav_artists)]).index).unique()
        for idx in idxs_fav_art_songs:
            songs_w_simsRats = list(enumerate(matrix[idx]))
            songs_w_simsRats = [x for x in songs_w_simsRats if x[1] < 1.0]
            songs.extend(songs_w_simsRats)
        songs = sorted(songs_w_simsRats, key=lambda pair: pair[1], reverse=True)
        songs = [x[0] for x in songs if x[0] not in list(idxs_fav_art_songs)]
        self.songs_to_ask = list(dict.fromkeys(songs))
        ln_idxs = len(idxs_fav_art_songs)
        ln_songs = len(self.songs_to_ask)
        new_idxs = np.random.randint(0, ln_songs, ln_idxs)
        for x in range(ln_idxs): 
            self.songs_to_ask.insert(new_idxs[x], idxs_fav_art_songs[x])

    def get_song(self, index):
        dataFrame = self.user.get_df()
        row = dataFrame.iloc[index]
        name = row[dataFrame.columns[2]]
        artist = row[dataFrame.columns[1]]
        return f'{name} by {artist}' 

    def initialize(self):
        songs = self.songs_to_ask
        idx = self.num_songs_asked
        self.path_to_SP.song.name = str(songs[idx])
        self.path_to_SP.song.text = self.get_song(songs[idx])
        self.num_songs_asked += 1
    
    def make_decision(self, instance):
        name = self.path_to_SP.song.name
        idx = int(name)
        self.user.add_review(idx, int(instance.text))
        isEnoughDecisions = self.user.get_songThresholdReached()
        rev_count = len(self.user.get_reviewed())
        if (not isEnoughDecisions) and (rev_count >= 20):
            # self.ids.toPlaylist.text = 'Make Playlist'
            self.ids.toPlaylist.font_size = 30
            self.ids.toPlaylist.on_press = self.goToPlaylist
            self.user.set_songThresholdReached(True)
        if rev_count % 5 == 0: self.resetSTA()    
        self.initialize()

    def resetSTA(self):
        self.user.set_df(self.web_data.giveDfPredictions(self.user.get_df()))
        df = self.user.get_df()
        df_wo_rev = df[df['Review'].isna()]
        self.num_songs_asked = 0
        self.songs_to_ask = list((df_wo_rev.sort_values(by=['Predictions'], ascending=False)).index)
        print(df_wo_rev.sort_values(by=['Predictions'], ascending=False))

    def goToPlaylist(self):
        self.ids.WM.current = 'Playlist Page'

    """

    Playlist Page Functions:
        make_playlist

    """

    def make_playlist(self):
        layout = GridLayout(cols=1, rows=10)
        self.user.make(self.web_data)
        for song in self.user.get_playlist():
            song = self.get_song(song)
            if len(song) > 30: 
                song = f'{song[:30]}...' 
            cur_button = Button(text=song, 
                                font_size=25,
                                size_hint=(.2, .05), 
                                background_color='blue')
            # cur_button.bind()
            # in the future we would bind a function that plays a 30 second snippet of the song
            layout.add_widget(cur_button)
        self.path_to_PP.bx.add_widget(layout)
   
    pass

class myApp(MDApp):
    def build(self):
        return MainWindow()

if __name__ == "__main__":
    st = myApp()
    st.run()