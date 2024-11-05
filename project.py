import pandas as pd
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
# Set maximum rows to None (no truncation)
pd.set_option('display.max_rows', None)

# Set maximum columns to None (no truncation)
pd.set_option('display.max_columns', None)
# teams_merged = pd.merge(teams_data, teams_post_data, on=['tmID', 'year'], how='left')

#pmerged_df = pd.merge(teams, coaches, on='tmID', how='left', validate="many_to_many")  # you can also use 'left', 'right', or 'outer' depending on your needsDIDteam_
#print(pmerged_df.head())

def clear_players(players):
    players = players.drop(["pos", "deathDate", "birthDate"], axis=1)
    players.rename(columns={"bioID": "playerID"}, inplace=True)
    return players

def clear_awards(awards):
    awards = awards[(awards["award"] != "Kim Perrot Sportmanship") & (awards["award"] != "Kim Perrot Sportmanship Award")]
    return awards

def clear_teams(teams):
    teams = teams.drop(["lgID", "divID", "seeded", "confID", "name", "arena" ], axis=1) #confID, arena?
    return teams

def clear_coaches(coaches):
    coaches = coaches.drop(["lgID"], axis=1) #TODO: see year
    coaches.rename(columns={'won': 'coach_won', 'lost':'coach_lost'}, inplace=True)
    return coaches

def clear_players_teams(players_teams):
    players_teams = players_teams.drop(["lgID"], axis=1) #TODO: see year
    return players_teams

def clear_series_post(series_post):
    series_post = series_post.drop(["lgIDWinner", "lgIDLoser"], axis=1) #TODO: see year
    return  series_post

def clear_teams_post(teams_post):
    teams_post = teams_post.drop(["lgID"],axis=1)
    return  teams_post


awards_players = clear_awards(pd.read_csv('data/awards_players.csv'))
coaches = clear_coaches(pd.read_csv('data/coaches.csv'))
players_teams = clear_players_teams(pd.read_csv('data/players_teams.csv'))
players = clear_players(pd.read_csv('data/players.csv'))
series_post = clear_series_post(pd.read_csv('data/series_post.csv'))
teams_post = clear_teams_post(pd.read_csv('data/teams_post.csv'))
df = clear_teams(pd.read_csv('data/teams.csv'))


#merged_teams = pd.merge(merged_teams, series_post, on=["tmID", 'year'])
#print(merged_teams)

# awards_count = awards_players.groupby('playerID').size().reset_index(name='awards_count')
# #print(awards_count)
# players = players.merge(awards_count, on=['playerID'], how='left')
# players["awards_count"].fillna(0, inplace=True)
# 
# #print(players.sort_values("awards_count", ascending=False).head())
# 
# players_teams_merged = players.merge(players_teams, on=['playerID'])
# #print(players_teams_merged.head())
# team_awards = players_teams_merged.groupby(["tmID"])["awards_count"].sum().reset_index()
# 
# 
# df = df.merge(team_awards, on=['tmID'])
# df["awards_count"].fillna(0, inplace=True)

# Step 1: Calculate the total awards per player for each year
# Assuming 'award' is the column that lists the awards
player_awards_by_year = awards_players.groupby(['playerID', 'year']).size().reset_index(name='awards_count')

# Step 2: Apply a cumulative sum to get the total awards by year for each player
player_awards_by_year['cumulative_awards'] = player_awards_by_year.groupby('playerID')['awards_count'].cumsum()

# Example output columns: ['playerID', 'yearID', 'awards_count', 'cumulative_awards']

# Step 3: Merge cumulative player awards with team_players data
team_players_awards = pd.merge(players_teams, player_awards_by_year[['playerID', 'year', 'cumulative_awards']],
                               on=['playerID', 'year'], how='left')

# Fill missing values (for players with no awards) with 0
team_players_awards['cumulative_awards'].fillna(0, inplace=True)

# Step 4: Group by team and year to sum the cumulative awards for each team
team_awards_by_year = team_players_awards.groupby(['tmID', 'year'])['cumulative_awards'].sum().reset_index()

# Example output columns: ['tmID', 'yearID', 'cumulative_awards']

# Step 5: Merge cumulative team awards into your main dataframe
df = df.merge(team_awards_by_year, on=['tmID', 'year'], how='left')

# Fill any missing awards with 0
df['cumulative_awards'].fillna(0, inplace=True)


df = df.sort_values(by=['franchID', 'year'])
df['playoffNextYear'] = df['playoff'].shift(-1)
df.loc[df['franchID']!= df['franchID'].shift(-1),'playoffNextYear'] = None
df.dropna(subset= ['playoffNextYear'], inplace=True)

df['playoff'] = df['playoff'] == 'Y'
df = pd.merge(df, teams_post, on=["tmID", 'year'], how='left')
df.fillna(0, inplace=True)
df = pd.merge(df, coaches, on=["tmID", 'year'], how='left')

all_time_best_players = players_teams.groupby('playerID')["points"].sum().reset_index().sort_values(by=['points'], ascending=False)
top_all_time_best_players = all_time_best_players.merge(players_teams, on=['playerID']).groupby('playerID')
top_all_time_best_players = top_all_time_best_players.head(5)

tmid_counts = top_all_time_best_players['tmID'].value_counts().reset_index()
tmid_counts.columns = ['tmID', 'tmID_count']

tmid_counts = tmid_counts.rename(columns={'tmID_count': 'number_of_top_players'})

df = df.merge(tmid_counts, on=['tmID'], how='left')
df['number_of_top_players'].fillna(0, inplace=True)

# top_all_time_best_players["has_top_player"] = True
# df = df.merge(top_all_time_best_player]s, on=['tmID', 'year'], how='left')

# print(df)

# print(df[df["has_top_player"] == False])

# print(top_all_tie_best_players.head(5))
# print(all_time_best_players.columns.tolist())
# all_time_best_players = all_time_best_players.merge(players_teams, on=['playerID'])
# print(all_time_best_players.head(5))
# df = pd.merge(df, all_time_best_players, on=['tmID']) 

# print(df.head(5))
# print(df.columns.tolist())

features = ['won', 'lost','playoff', 'W','L', "coach_won", "coach_lost", "cumulative_awards", "number_of_top_players" ]

target = 'playoffNextYear'
# Splitting data into training (earlier seasons) and testing (recent seasons)
# Assuming year 5 is an arbitrary cutoff for training vs test data
train_data = df[df.year <= 6].copy()  # Earlier seasons
test_data = df[df.year > 6].copy()    # Recent seasons

X_train = train_data[features]
y_train = train_data[target]

X_test = test_data[features]
y_test = test_data[target]

models = []
models.append(('LR', LogisticRegression(max_iter=1000)))
models.append(('SVC', SVC()))
models.append(('DTC', DecisionTreeClassifier()))
models.append(('KNN', KNeighborsClassifier()))
models.append(('GNB', GaussianNB()))
models.append(('MLP', MLPClassifier(max_iter=600)))
models.append(('RFC', RandomForestClassifier()))
models.append(('ABC', AdaBoostClassifier(algorithm='SAMME')))
models.append(('GBC', GradientBoostingClassifier()))


# Train and evaluate each model
results = {}
for name, model in models:
    # Train the model
    model.fit(X_train, y_train)
    print(model)
    # Predict on the test data
    y_pred = model.predict(X_test)
    # y_pred = model.predict_proba(X_test)

    # y_pred_wins = y_pred[:,1]

    # Evaluate the accuracy
    accuracy = accuracy_score(y_test,y_pred)

    # Store the result
    results[name] = accuracy
    print(f'{name} Accuracy: {accuracy * 100:.2f}%')

# Make predictions for the next season using the best model
# For simplicity, let’s assume you want to predict with the last model in the list
best_model = models[-1][1]  # Example: MLPClassifier
next_season = test_data[test_data.year == 9]  # Replace '6' with the next season
X_next_season = next_season[features]

next_season_predictions = best_model.predict(X_next_season)
# next_season_predictions = best_model.predict_proba(X_next_season)
next_season['predicted_playoff'] = next_season_predictions
# next_season['predicted_playoff'] = next_season_predictions[:,1]

# Output predictions for the next season
print(next_season[['franchID', 'year', 'predicted_playoff']])
