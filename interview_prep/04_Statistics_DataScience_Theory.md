# 📊 Data Science, Statistics & Probability - Theory Guide (10 Years Experience)

---

## 📌 Table of Contents
1. [Statistics Fundamentals](#1-statistics-fundamentals)
2. [Probability Theory](#2-probability-theory)
3. [Probability Distributions](#3-probability-distributions)
4. [Hypothesis Testing](#4-hypothesis-testing)
5. [Bayesian Statistics](#5-bayesian-statistics)
6. [Exploratory Data Analysis (EDA)](#6-exploratory-data-analysis)
7. [Data Engineering Basics](#7-data-engineering-basics)
8. [Interview Questions & Answers](#8-interview-questions--answers)

---

## 1. Statistics Fundamentals

### 1.1 Descriptive vs Inferential Statistics

**Descriptive:** Data ko summarize karna (mean, median, mode, charts)
**Inferential:** Sample se population ke baare mein conclusions nikalna (hypothesis testing, confidence intervals)

### 1.2 Measures of Central Tendency

| Measure | Description | When to Use |
|---------|-------------|-------------|
| **Mean** | Sum/Count — average value | Symmetric data, no outliers |
| **Median** | Middle value (sorted) | Skewed data, outliers present |
| **Mode** | Most frequent value | Categorical data |

**Mean vs Median:**
- Normal distribution mein: Mean = Median = Mode
- Right-skewed: Mean > Median (outliers pull mean right)
- Left-skewed: Mean < Median
- Salary data mein median better hai (few very high salaries skew mean)

### 1.3 Measures of Dispersion

| Measure | Description |
|---------|-------------|
| **Range** | Max - Min (simplest, sensitive to outliers) |
| **Variance (σ²)** | Average squared deviation from mean |
| **Standard Deviation (σ)** | √Variance (same unit as data) |
| **IQR** | Q3 - Q1 (middle 50% spread, outlier robust) |
| **Coefficient of Variation** | (σ/μ) × 100% — relative variability |

**Sample vs Population:**
- Population variance: σ² = Σ(xᵢ-μ)²/N
- Sample variance: s² = Σ(xᵢ-x̄)²/(n-1) — Bessel's correction (n-1)
- n-1 kyun? Sample variance biased hota hai, n-1 se unbiased estimate milta hai

### 1.4 Percentiles & Quartiles
- **Q1 (25th percentile):** 25% data isse chhota
- **Q2 (50th percentile):** Median
- **Q3 (75th percentile):** 75% data isse chhota
- **IQR = Q3 - Q1**
- **Outlier detection:** < Q1 - 1.5×IQR ya > Q3 + 1.5×IQR

### 1.5 Correlation

**Pearson Correlation (r):**
- Linear relationship measure (-1 to +1)
- r = 1: Perfect positive linear, r = -1: Perfect negative linear, r = 0: No linear
- Assumption: Both variables normal, linear relationship
- **Correlation ≠ Causation!** (bahut important interview point)

**Spearman Correlation:**
- Rank-based, monotonic relationships ke liye
- Non-linear mein bhi kaam karta hai
- Ordinal data ke liye suitable

**Kendall's Tau:**
- Rank-based, small sample sizes ke liye
- Concordant/discordant pairs pe based

### 1.6 Covariance vs Correlation
- **Covariance:** Direction (positive/negative) batata hai, scale depend karta hai — compare nahi kar sakte
- **Correlation:** Covariance ko normalize karta hai — -1 to +1 range, comparable

---

## 2. Probability Theory

### 2.1 Basic Concepts

| Term | Meaning |
|------|---------|
| **Sample Space (S)** | Sabhi possible outcomes ka set |
| **Event** | Sample space ka subset |
| **P(A)** | Event A ki probability (0 to 1) |
| **Complement P(A')** | 1 - P(A) |
| **Union P(A∪B)** | A ya B ho |
| **Intersection P(A∩B)** | A aur B dono ho |

### 2.2 Types of Probability
- **Classical:** Equally likely outcomes: P(A) = favorable/total
- **Empirical/Frequentist:** Experiments se: P(A) = frequency/total trials
- **Subjective:** Expert judgment based

### 2.3 Probability Rules

**Addition Rule:**
- P(A∪B) = P(A) + P(B) - P(A∩B)
- Mutually exclusive: P(A∪B) = P(A) + P(B)

**Multiplication Rule:**
- Independent: P(A∩B) = P(A) × P(B)
- Dependent: P(A∩B) = P(A) × P(B|A)

**Conditional Probability:**
- P(A|B) = P(A∩B) / P(B)
- "B hone ke baad A ki probability"

### 2.4 Bayes' Theorem

**Formula:** P(A|B) = P(B|A) × P(A) / P(B)

**Terms:**
- P(A|B) = Posterior probability
- P(A) = Prior probability
- P(B|A) = Likelihood
- P(B) = Evidence / Marginal probability

**Classic Example: Medical Test**
- Disease prevalence: 1% (Prior)
- Test sensitivity: 99% (True positive rate)
- Test specificity: 99% (True negative rate)
- Positive test → Actual disease probability?
  - P(Disease|Positive) = (0.99 × 0.01) / (0.99×0.01 + 0.01×0.99) = 50%!
  - Ye counter-intuitive hai but correct — rare disease ke saath false positive bhi count hota hai

### 2.5 Independence vs Conditional Independence
- **Independent:** P(A∩B) = P(A) × P(B) — ek ka hona dusre ko affect nahi karta
- **Conditional Independence:** P(A∩B|C) = P(A|C) × P(B|C) — C given hone pe A aur B independent hain
- Naive Bayes isi assumption pe based hai

### 2.6 Law of Large Numbers & Central Limit Theorem

**Law of Large Numbers:**
- Sample size badhne pe sample mean population mean ke paas jaata hai
- Jitne zyada experiments, utna accurate estimate

**Central Limit Theorem (CLT) — VERY IMPORTANT:**
- Kisi bhi distribution se random samples ka MEAN approximately NORMAL distribution follow karta hai (n ≥ 30)
- Sample mean ka distribution: Mean = μ, Std = σ/√n
- Ye hypothesis testing ki foundation hai
- Original distribution chahe kuch bhi ho — CLT laagu hoti hai!

---

## 3. Probability Distributions

### 3.1 Discrete Distributions

**Bernoulli:** Single binary trial (success/failure)
- P(X=1) = p, P(X=0) = 1-p
- Example: Coin toss

**Binomial:** n independent Bernoulli trials mein k successes
- P(X=k) = C(n,k) × pᵏ × (1-p)ⁿ⁻ᵏ
- Mean = np, Variance = np(1-p)
- Example: 10 coin tosses mein 7 heads ki probability

**Poisson:** Fixed time/space mein events ki count
- P(X=k) = (λᵏ × e⁻λ) / k!
- Mean = Variance = λ
- Example: Ek ghante mein kitne customers aayenge
- Condition: Events independent, constant rate, rare

**Geometric:** Pehli success tak kitne trials
- P(X=k) = (1-p)ᵏ⁻¹ × p
- Memoryless property!

### 3.2 Continuous Distributions

**Normal (Gaussian):**
- Bell-shaped, symmetric
- Defined by μ (mean) and σ (standard deviation)
- 68-95-99.7 Rule: 1σ mein 68%, 2σ mein 95%, 3σ mein 99.7% data
- Z-score: z = (x-μ)/σ (standard normal mein convert)
- Many natural phenomena follow this (height, weight, errors)

**Standard Normal:** Mean = 0, Std = 1
- Z-table se probabilities find kar sakte hain

**Uniform:** Sabhi values equally likely
- Continuous: f(x) = 1/(b-a) for a ≤ x ≤ b
- Example: Random number generator

**Exponential:** Events ke beech ka time (Poisson ka complement)
- P(X ≤ x) = 1 - e⁻λˣ
- Memoryless property
- Example: Next customer aane mein kitna time lagega

**Log-Normal:** log(X) normal ho — right-skewed data (incomes, stock prices)

**Chi-Square (χ²):**
- k normal variables ke squares ka sum
- Goodness of fit test mein use
- Degrees of freedom = k

**t-Distribution (Student's t):**
- Normal jaisa but heavier tails
- Small samples (n < 30) ke liye
- n badhne pe normal ke paas jaata hai

**F-Distribution:**
- Two chi-square variables ka ratio
- ANOVA mein use hota hai

---

## 4. Hypothesis Testing

### 4.1 Basic Framework

**Steps:**
1. **Null Hypothesis (H₀):** Default assumption (no effect, no difference)
2. **Alternative Hypothesis (H₁):** Jo prove karna chahte hain
3. **Significance Level (α):** Typically 0.05 (5% risk of false positive)
4. **Test Statistic** calculate karo
5. **P-value** find karo
6. **Decision:** p-value < α → Reject H₀, else → Fail to reject H₀

**Important:** "Fail to reject H₀" ≠ "Accept H₀"! Absence of evidence ≠ Evidence of absence.

### 4.2 Types of Errors

| | H₀ True (no effect) | H₀ False (effect exists) |
|---|---|---|
| **Reject H₀** | Type I Error (α) - False Positive | Correct (Power = 1-β) |
| **Fail to reject H₀** | Correct | Type II Error (β) - False Negative |

- **Type I (α):** Effect nahi hai but bola hai (false alarm). Significance level se control hota hai.
- **Type II (β):** Effect hai but miss ho gaya. Power increase karke reduce karo (more data).
- **Power = 1-β:** Actual effect detect karne ki ability

### 4.3 P-value
- H₀ true hone ke assumption pe observed data (ya usse extreme) ki probability
- Low p-value = evidence against H₀
- P-value ≠ H₀ true hone ki probability! (common misconception)
- P < 0.05: Statistically significant (convention)
- P < 0.01: Highly significant
- Statistical significance ≠ Practical significance

### 4.4 Common Tests

| Test | Use Case | Data Type |
|------|----------|-----------|
| **Z-test** | Mean compare (σ known, n ≥ 30) | Continuous |
| **t-test (one-sample)** | Sample mean vs known value | Continuous |
| **t-test (two-sample)** | Two group means compare | Continuous |
| **Paired t-test** | Same group, before-after | Continuous |
| **ANOVA** | 3+ group means compare | Continuous |
| **Chi-square** | Categorical variables association | Categorical |
| **Chi-square Goodness of Fit** | Distribution fit test | Categorical |
| **Mann-Whitney U** | Non-parametric two groups | Ordinal/Continuous |
| **Wilcoxon** | Non-parametric paired | Ordinal/Continuous |
| **Kruskal-Wallis** | Non-parametric 3+ groups | Ordinal/Continuous |
| **Fisher's Exact** | 2×2 contingency, small samples | Categorical |
| **KS Test** | Distribution comparison | Continuous |

### 4.5 ANOVA (Analysis of Variance)
- 3 ya zyada groups ke means compare karna
- H₀: Sab groups ke means equal hain
- F-statistic = Between-group variance / Within-group variance
- High F = groups significantly different
- **One-way ANOVA:** Ek factor (e.g., 3 treatments)
- **Two-way ANOVA:** Do factors (e.g., treatment + gender)
- Post-hoc tests (Tukey, Bonferroni): Specific groups mein difference find karna

### 4.6 Multiple Testing Problem
- 20 tests karo α=0.05 pe, toh 1 false positive expected hai
- **Bonferroni Correction:** α/n use karo (conservative)
- **FDR (False Discovery Rate):** Benjamini-Hochberg procedure (less conservative)

### 4.7 A/B Testing (Tech Interviews mein bahut pucha jaata hai)

**Process:**
1. Hypothesis define karo (new feature conversions badhayega)
2. Metric choose karo (conversion rate, revenue, CTR)
3. Sample size calculate karo (power analysis)
4. Users randomly split karo (control vs treatment)
5. Experiment chalne do (adequate duration)
6. Statistical test karo (t-test, proportion test)
7. Decision lo

**Common Pitfalls:**
- Peeking at results (stopping early biases results)
- Simpson's Paradox (aggregate vs segment level contradictions)
- Novelty effect (new = exciting, effect temporary ho sakta hai)
- Not accounting for multiple metrics
- Sample Ratio Mismatch (groups unequal ho jayen)
- Interference between groups (network effects, marketplace effects)

**Sample Size Calculation needs:** α (significance), β (power), MDE (minimum detectable effect), baseline rate

---

## 5. Bayesian Statistics

### 5.1 Bayesian vs Frequentist

| Frequentist | Bayesian |
|------------|----------|
| Probability = long-run frequency | Probability = degree of belief |
| Parameters fixed, data random | Parameters random (distribution), data fixed |
| Point estimates (MLE) | Probability distributions (posterior) |
| P-values, confidence intervals | Credible intervals |
| No prior knowledge used | Prior knowledge explicitly incorporated |

### 5.2 Bayesian Framework
- **Prior:** Parameter ke baare mein pehle se belief
- **Likelihood:** Data given parameter ki probability
- **Posterior:** Data dekhne ke baad updated belief
- **Posterior ∝ Likelihood × Prior**

### 5.3 Conjugate Priors
- Prior aur posterior same distribution family ke hon
- Beta-Binomial, Normal-Normal, Gamma-Poisson
- Computationally convenient

### 5.4 Bayesian A/B Testing
- Directly P(B > A) calculate karo — zyada intuitive
- "Treatment better hone ki 95% probability hai" vs "p-value < 0.05"
- Prior se start karo, data aate jaaye posterior update karo
- Sample size flexibility — fixed sample ki zaroorat nahi

---

## 6. Exploratory Data Analysis (EDA)

### 6.1 EDA Steps
1. Data shape, types, basic statistics dekho
2. Missing values identify karo
3. Distribution of each variable (histogram, boxplot)
4. Outliers detect karo
5. Relationships between variables (scatter, correlation)
6. Target variable analysis
7. Feature engineering ideas note karo

### 6.2 Visualization Types

| Plot | Use Case |
|------|----------|
| **Histogram** | Single variable distribution |
| **Box Plot** | Distribution + outliers + quartiles |
| **Scatter Plot** | Two variables relationship |
| **Heatmap** | Correlation matrix visualize |
| **Bar Chart** | Categorical frequency |
| **Line Chart** | Time series trends |
| **Violin Plot** | Distribution + density |
| **Pair Plot** | All pairwise relationships |
| **QQ Plot** | Normality check |

### 6.3 Outlier Detection Methods
- **IQR method:** < Q1-1.5×IQR ya > Q3+1.5×IQR
- **Z-score:** |z| > 3 (assuming normal distribution)
- **Modified Z-score:** Uses median (robust)
- **Isolation Forest:** Anomaly detection algorithm
- **DBSCAN:** Noise points as outliers
- **Domain knowledge:** Kya ye value possible hai?

---

## 7. Data Engineering Basics

### 7.1 SQL (Interview mein zaroor pucha jaata hai)

**Key Concepts:**
- **JOINs:** INNER, LEFT, RIGHT, FULL OUTER, CROSS, SELF
- **GROUP BY:** Aggregate functions ke saath (COUNT, SUM, AVG, MAX, MIN)
- **HAVING:** GROUP BY ke baad filter
- **Window Functions:** ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, NTILE
- **Subqueries:** Nested queries
- **CTEs:** WITH clause for readability
- **UNION vs UNION ALL:** Duplicate handling

**Common Interview SQL Questions:**
- Second highest salary find karo
- Duplicate rows detect karo
- Running total calculate karo (window function)
- Customers jo kabhi order nahi kiye (LEFT JOIN + NULL check)
- Year-over-year growth (LAG function)

### 7.2 Big Data Concepts

| Technology | Purpose |
|-----------|---------|
| **Hadoop** | Distributed storage (HDFS) + processing (MapReduce) |
| **Spark** | Fast distributed processing (in-memory), ML (MLlib) |
| **Kafka** | Real-time data streaming |
| **Airflow** | Workflow orchestration (DAGs) |
| **dbt** | Data transformation (SQL-based) |
| **Snowflake/BigQuery/Redshift** | Cloud data warehouses |

### 7.3 Data Quality Dimensions
- **Completeness:** Missing values nahi hone chahiye
- **Accuracy:** Values correct hone chahiye
- **Consistency:** Same data sabhi systems mein same
- **Timeliness:** Data up-to-date ho
- **Uniqueness:** No duplicate records
- **Validity:** Data constraints follow kare (format, range)

---

## 8. Interview Questions & Answers

### Q1: Central Limit Theorem explain karein aur kyun important hai?
**Answer:**
- Kisi bhi distribution se random samples ka MEAN approximately normal distribution follow karta hai jab sample size sufficient ho (n ≥ 30)
- Mean of sample means = Population mean (μ)
- Standard error = σ/√n
- Important kyunki: Most hypothesis tests normal distribution assume karte hain — CLT guarantee karta hai ki ye valid hai large samples ke liye, original distribution chahe kuch bhi ho

### Q2: P-value ko ek common person ko kaise explain karoge?
**Answer:**
- Maan lo treatment ka koi effect nahi hai (null hypothesis true)
- P-value batata hai ki agar sach mein koi effect nahi hai, toh jo result humne observe kiya (ya usse extreme), wo kitni likely hai
- Low p-value (< 0.05) matlab: ye result by chance bahut unlikely hai, toh shayad sach mein kuch effect hai
- P-value ye NAHI batata ki hypothesis sahi hai ya galat

### Q3: Correlation vs Causation ka difference explain karein with example.
**Answer:**
- **Correlation:** Do variables saath mein change hote hain
- **Causation:** Ek variable dusre ko cause karta hai
- Example: Ice cream sales aur drowning deaths correlated hain — but ice cream drowning cause nahi karta! Dono ka common cause garam mausam hai (confounding variable)
- Causation prove karne ke liye: Randomized Controlled Trials (RCTs), ya causal inference methods (IV, diff-in-diff, RDD)

### Q4: Type I vs Type II error — real-world example do.
**Answer:**
- **Type I (False Positive):** Court mein innocent person ko guilty declare karna. Alarm when no fire.
- **Type II (False Negative):** Guilty person ko innocent declare karna. Fire but no alarm.
- Medical test: Type I = healthy person ko patient bolo (unnecessary treatment). Type II = patient ko healthy bolo (treatment miss, potentially fatal)
- Usually Type II zyada dangerous hai (cancer miss karna), but depends on context

### Q5: A/B test design karein: new checkout button ka effect on conversion rate.
**Answer:**
1. **Hypothesis:** H₀: Conversion rate same, H₁: New button se conversion rate different
2. **Metric:** Primary: Conversion rate. Secondary: Revenue per user, cart abandonment
3. **Sample Size:** Power analysis se calculate — α=0.05, power=0.8, MDE=2% uplift, baseline=10% conversion → ~3800 users per group
4. **Randomization:** Users randomly 50-50 split. Check for sample ratio mismatch.
5. **Duration:** Minimum 1-2 weeks (cover weekly patterns). Don't peek early.
6. **Analysis:** Proportion z-test. Check segments (mobile vs desktop). Report confidence interval, not just p-value.
7. **Pitfalls avoid:** Novelty effect, early stopping, network effects

### Q6: Normal distribution ke properties batao.
**Answer:**
- Bell-shaped, symmetric around mean
- Mean = Median = Mode
- Fully defined by μ aur σ
- 68-95-99.7 rule (1σ, 2σ, 3σ)
- Area under curve = 1
- Infinite range (-∞ to +∞)
- Sum of normals bhi normal
- CLT ki wajah se naturally zaroori
- Many statistical tests assume normality

### Q7: Confidence Interval vs Prediction Interval ka difference?
**Answer:**
- **Confidence Interval (CI):** Population parameter (e.g., mean) ka range — "95% confident ki true mean is range mein hai"
- **Prediction Interval (PI):** Next individual observation ka range — always CI se wider
- CI = uncertainty about mean/parameter
- PI = CI + individual variation
- Example: Average height CI = 170-175cm. Next person's height PI = 155-190cm.

### Q8: Simpson's Paradox explain karein.
**Answer:**
- Aggregate data mein ek trend dikhta hai, but subgroups mein OPPOSITE trend dikhta hai
- Example: Hospital A ka overall survival rate Hospital B se kam hai. But har disease category mein A better hai! Kyun? A ko zyada serious cases aate hain.
- Lesson: Always segment-wise analysis karo. Confounding variables check karo.
- A/B testing mein bhi ho sakta hai — overall result segment results se contradict kare

### Q9: Feature importance aur feature selection ka difference?
**Answer:**
- **Feature Importance:** Model batata hai ki kaunsa feature kitna important hai (coefficients, tree-based importance, SHAP values). Model train hone ke baad.
- **Feature Selection:** Training se PEHLE irrelevant/redundant features remove karo. Methods: Filter (correlation, mutual information), Wrapper (RFE), Embedded (L1 regularization).
- Ye complementary hain — importance se selection decide kar sakte hain

### Q10: Explain the difference between MLE and MAP estimation.
**Answer:**
- **MLE (Maximum Likelihood Estimation):** Data ko best explain karne wale parameters find karo. P(Data|θ) maximize karo. No prior, purely data-driven.
- **MAP (Maximum A Posteriori):** MLE + Prior belief. P(θ|Data) ∝ P(Data|θ) × P(θ) maximize karo.
- MLE with uniform prior = MAP
- MAP = regularized MLE (L2 regularization = Gaussian prior, L1 = Laplace prior)
- MLE overfit ho sakta hai small data pe, MAP prior se regularize karta hai

### Q11: What is survivorship bias and how does it affect data science?
**Answer:**
- Sirf "surviving" entities ko analyze karna, failed/filtered entities ko ignore karna
- Example: Successful startups ka analysis — failed startups data mein nahi hain, conclusions biased
- WWII aircraft: Returning planes ke bullet holes dekhe → reinforce areas WITHOUT holes (missing planes wahan hit hue!)
- Data Science mein: Churn analysis — sirf active users ka data hai, churned users ka behavior miss ho raha

### Q12: What is semantic meaning of R-squared?
**Answer:**
- R² = 1 - (SS_residual / SS_total)
- Kitna percentage of total variance model explain karta hai
- R² = 0.85 means model 85% variance explain karta hai
- R² = 0: Model sirf mean predict kar raha (baseline)
- R² < 0: Model mean se bhi bura hai (possible in test set)
- **Adjusted R²:** Extra features add karne pe penalty — honest estimate
- Limitation: R² high but model still wrong ho sakta hai (wrong functional form)

---

## Quick Revision Table

| Concept | Key Point |
|---------|-----------|
| CLT | Sample means approximately normal (n ≥ 30) |
| P-value | Probability of data given H₀ true |
| Type I Error | False Positive (α) |
| Type II Error | False Negative (β) |
| Power | 1 - β (ability to detect effect) |
| Bayes Theorem | P(A\|B) = P(B\|A)×P(A)/P(B) |
| Correlation ≠ Causation | Common cause, reverse causation possible |
| Normal Distribution | Bell curve, 68-95-99.7 rule |
| A/B Testing | Randomized experiment, control vs treatment |
| Simpson's Paradox | Aggregate vs subgroup trends opposite |
| Bias-Variance | Underfitting vs Overfitting |
| R² | Proportion of variance explained |
| MLE | Maximize P(Data\|θ) |
| Confidence Interval | Parameter range estimate |

---

*10+ Years Experience Level - Statistics & Data Science Theory*
