from pycaret.regression import *
import pmdarima as pm
from pmdarima.arima import ARIMA

def run_auto_ml(train_df, test_df, target_col, feature_cols, normal_transform, ml_criteria):
    # Model Definitions
    s = setup(data = train_df,
              test_data = test_df,
              target = target_col,
              fold_strategy = 'timeseries',
              numeric_features = feature_cols,
              fold = 3,
              transform_target = normal_transform,
              feature_selection = True,
              feature_selection_threshold = 0.8,
              remove_multicollinearity = True,
              multicollinearity_threshold = 0.9,
              session_id = 123)
    best = compare_models(sort = ml_criteria)
    results = pull()
    model_results = results.Model.tolist()
    print(type(best))
    return best

def get_important_features(get_config, best):
    # Get list of features and their values
    features = pd.DataFrame({'Feature': get_config('X_train').columns,
                             'Variable Importance' : abs(best.coef_)}).sort_values(by='Variable Importance', ascending=False)
    features['Variable Importance'] = features['Variable Importance'].astype(float)

    # Here we want to get features with an absolute value variable importance score of 1 or greater
    features = features[features['Variable Importance'] >= 1]
    features = features.reset_index(drop=True)
    return features

def run_auto_arima(df, feature_cols, pred_start_dt, forecast_window):
    pred_df = pd.DataFrame()
    dti = pd.date_range(pred_start_dt, periods=forecast_window, freq="M")
    dti = dti + pd.offsets.MonthBegin(-1)
    pred_df['Calendar Date'] = dti

    for col in feature_cols:

        model = pm.auto_arima(df[col],
                              start_p=1,
                              start_q=1,
                              max_p=5,
                              max_q=5,
                              m=12,
                              start_P=0,
                              seasonal=True,
                              d=1,
                              D=1,
                              trace=True,
                              error_action='ignore',  # don't want to know if an order does not work
                              suppress_warnings=True,  # don't want convergence warnings
                              stepwise=True)  # set to stepwise

        # make future predictions
        pred_df[col] = model.predict(n_periods=forecast_window)
    return pred_df

def compute_apes_and_mapes(df, date_col, target_col, feature_cols):
    sort_cols = [date_col, target_col]
    ape_cols = []
    for col in feature_cols:
        ape_col = col+' - APE'
        df[ape_col] = ((df[target_col] - df[col]).abs())/df[target_col]
        sort_cols.append(col)
        sort_cols.append(ape_col)
        ape_cols.append(ape_col)
    df = df[sort_cols]
    non_ape_cols = list(set(sort_cols) - set(ape_cols))
    mape_df = df.groupby([True]*len(df)).mean(numeric_only=True)
    mape_df[non_ape_cols] = np.nan
    df = pd.concat([df,mape_df])
    return df