using System.Globalization;

var builder = WebApplication.CreateBuilder(args);

// allow the React dashboard (running locally) to call this API
builder.Services.AddCors(options =>
    options.AddDefaultPolicy(policy =>
        policy.WithOrigins("http://localhost:5173", "http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod()));

var app = builder.Build();
app.UseCors();

// predictions.csv comes from the Databricks notebook (train_model.py)
var path = builder.Configuration["PredictionsPath"] ?? "../../data/predictions.csv";

if (!File.Exists(path))
{
    throw new FileNotFoundException($"Could not find {path}. Download predictions.csv from Databricks first.");
}

var readings = File.ReadAllLines(path)
    .Skip(1) // header
    .Where(line => !string.IsNullOrWhiteSpace(line))
    .Select(line => line.Split(','))
    .Select(p => new Reading(
        p[0],
        double.Parse(p[1], CultureInfo.InvariantCulture),
        double.Parse(p[2], CultureInfo.InvariantCulture),
        double.Parse(p[3], CultureInfo.InvariantCulture),
        p[4] == "1",
        p[5] == "1",
        double.Parse(p[6], CultureInfo.InvariantCulture)))
    .ToList();

app.MapGet("/health", () => new { status = "ok" });

// all readings, paged so the dashboard doesn't load everything at once
app.MapGet("/readings", (int? skip, int? limit) =>
    readings.Skip(skip ?? 0).Take(limit ?? 1000));

// only the readings the model flagged as abnormal
app.MapGet("/anomalies", () =>
    readings.Where(r => r.PredictedAnomaly));

// how well the model did compared with the simulated faults
app.MapGet("/summary", () =>
{
    var flagged = readings.Count(r => r.PredictedAnomaly);
    var actual = readings.Count(r => r.IsAnomaly);
    var correct = readings.Count(r => r.PredictedAnomaly && r.IsAnomaly);

    return new Summary(
        readings.Count,
        flagged,
        actual,
        flagged == 0 ? 0 : Math.Round((double)correct / flagged, 2),
        actual == 0 ? 0 : Math.Round((double)correct / actual, 2));
});

app.Run();

record Reading(
    string Timestamp,
    double TemperatureC,
    double VibrationMmS,
    double SpeedRpm,
    bool IsAnomaly,
    bool PredictedAnomaly,
    double Score);

record Summary(int Total, int Flagged, int ActualFaults, double Precision, double Recall);
