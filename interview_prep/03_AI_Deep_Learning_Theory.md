# 🧠 AI & Deep Learning - Complete Theory Guide (10 Years Experience)

---

## 📌 Table of Contents
1. [Artificial Intelligence Overview](#1-artificial-intelligence-overview)
2. [Neural Network Fundamentals](#2-neural-network-fundamentals)
3. [Convolutional Neural Networks (CNN)](#3-convolutional-neural-networks-cnn)
4. [Recurrent Neural Networks (RNN)](#4-recurrent-neural-networks-rnn)
5. [Transformers & Attention](#5-transformers--attention)
6. [Natural Language Processing (NLP)](#6-natural-language-processing-nlp)
7. [Generative AI](#7-generative-ai)
8. [Computer Vision](#8-computer-vision)
9. [Reinforcement Learning](#9-reinforcement-learning)
10. [MLOps & AI in Production](#10-mlops--ai-in-production)
11. [Interview Questions & Answers (50+)](#11-interview-questions--answers)

---

## 1. Artificial Intelligence Overview

### 1.1 AI kya hai?
Artificial Intelligence ka matlab hai machines ko aise intelligent behavior dena jo normally human intelligence se associated hota hai — reasoning, learning, perception, problem-solving, decision making.

### 1.2 AI ke Types

**Capability ke basis pe:**
| Type | Description | Example |
|------|-------------|---------|
| **Narrow/Weak AI** | Ek specific task mein expert | Siri, Chess AI, Spam Filter |
| **General/Strong AI** | Human-level intelligence, koi bhi task | Abhi exist nahi karta |
| **Super AI** | Human se superior intelligence | Theoretical/hypothetical |

**Functionality ke basis pe:**
| Type | Description |
|------|-------------|
| **Reactive Machines** | Sirf current input pe react kare, no memory (Deep Blue) |
| **Limited Memory** | Past data se seekhe (Self-driving cars, ChatGPT) |
| **Theory of Mind** | Emotions samjhe (Research stage) |
| **Self-aware** | Apni consciousness ho (Hypothetical) |

### 1.3 AI vs ML vs DL vs Data Science

```
AI (Artificial Intelligence)
 └── ML (Machine Learning) — data se patterns seekhna
      └── DL (Deep Learning) — deep neural networks se seekhna
           └── Generative AI — naya content generate karna

Data Science = Data analysis + Statistics + ML + Domain Knowledge + Visualization
```

**Key Differences:**
- **AI:** Broad field — koi bhi intelligent system
- **ML:** AI ka subset — data se rules seekhna (vs manually programming)
- **DL:** ML ka subset — multi-layered neural networks
- **GenAI:** DL ka subset — new content create karna (text, images, code)

### 1.4 AI Ethics & Responsible AI

**Key Principles:**
- **Fairness:** Model biased na ho against any group
- **Transparency:** Explainable decisions (XAI - Explainable AI)
- **Privacy:** User data protection (Differential Privacy, Federated Learning)
- **Accountability:** Who is responsible for AI decisions?
- **Safety:** AI systems ko harmful nahi hona chahiye
- **Robustness:** Adversarial attacks se protect karo

**Common Biases in AI:**
- Training data mein historical bias
- Sampling bias — data representative nahi
- Confirmation bias — model existing beliefs confirm kare
- Automation bias — humans AI pe blindly trust karein

---

## 2. Neural Network Fundamentals

### 2.1 Perceptron (Simplest Neural Network)

**Structure:** Input → Weights → Sum → Activation → Output

**How it works:**
1. Inputs ko weights se multiply karo
2. Sab ka sum lo + bias add karo: z = Σ(wᵢxᵢ) + b
3. Activation function se pass karo: output = f(z)

**Limitation:** Sirf linearly separable problems solve kar sakta hai (XOR nahi)
**Solution:** Multi-Layer Perceptron (MLP) - hidden layers add karo

### 2.2 Activation Functions

| Function | Formula | Range | Use Case |
|----------|---------|-------|----------|
| **Sigmoid** | 1/(1+e⁻ˣ) | (0,1) | Binary classification output |
| **Tanh** | (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ) | (-1,1) | Hidden layers (zero-centered) |
| **ReLU** | max(0,x) | [0,∞) | Most common hidden layer activation |
| **Leaky ReLU** | max(αx,x) | (-∞,∞) | Solves dying ReLU problem |
| **ELU** | x if x>0, α(eˣ-1) if x≤0 | (-α,∞) | Smooth, zero-centered |
| **GELU** | x·Φ(x) | (-∞,∞) | Transformers mein popular |
| **Swish** | x·sigmoid(x) | (-∞,∞) | Self-gated, smooth |
| **Softmax** | eˣⁱ/Σeˣʲ | (0,1), sum=1 | Multi-class classification output |

**Sigmoid ke problems:**
- **Vanishing Gradient:** Extreme values pe gradient nearly zero → deep networks train nahi hote
- **Not zero-centered:** Optimization slow
- **Expensive:** Exponential computation

**ReLU kyun popular hai:**
- Simple computation (fast)
- No vanishing gradient (positive side)
- Sparse activation (efficient)
- **Problem:** Dying ReLU — negative inputs pe permanently zero gradient

### 2.3 Backpropagation

**Concept:** Neural network ko train karne ka algorithm. Chain rule of calculus use karke har weight ka gradient calculate karta hai.

**Steps:**
1. **Forward Pass:** Input → layers through → prediction (ŷ)
2. **Loss Calculation:** Loss = L(y, ŷ) — actual vs predicted ka difference
3. **Backward Pass:** Loss se reverse mein chain rule se har weight ka gradient (∂L/∂w) calculate karo
4. **Weight Update:** w = w - learning_rate × gradient

**Key Concepts:**
- **Chain Rule:** ∂L/∂w₁ = ∂L/∂ŷ × ∂ŷ/∂z × ∂z/∂w₁
- **Computational Graph:** Forward pass ka graph banana, phir reverse mein gradients flow karna

### 2.4 Optimization Algorithms

| Optimizer | Description | Key Feature |
|-----------|-------------|-------------|
| **SGD** | Stochastic Gradient Descent | Simple, can escape local minima |
| **SGD + Momentum** | Previous gradients ka influence | Faster convergence, reduces oscillation |
| **AdaGrad** | Parameter-specific learning rates | Good for sparse features, decays fast |
| **RMSProp** | AdaGrad + exponential decay | Fixes AdaGrad's aggressive decay |
| **Adam** | RMSProp + Momentum | Most popular, adaptive learning rate |
| **AdamW** | Adam + decoupled weight decay | Better generalization |
| **LAMB** | Layer-wise adaptive, for large batch | Distributed training |

**Adam kyun popular hai:**
- Learning rate adapt hota hai har parameter ke liye
- Momentum use karta hai (past gradients remember)
- Default settings se bhi accha kaam karta hai
- Bias correction built-in

**Learning Rate:**
- Too high → diverge, oscillate, miss optimal point
- Too low → very slow convergence, stuck in local minima
- **Learning Rate Scheduling:** Start high, gradually decrease (cosine annealing, step decay, warm-up)

### 2.5 Loss Functions

**Classification:**
- **Binary Cross-Entropy:** -[y·log(ŷ) + (1-y)·log(1-ŷ)] — binary classification
- **Categorical Cross-Entropy:** -Σ yᵢ·log(ŷᵢ) — multi-class (one-hot encoded)
- **Sparse Categorical CE:** Same but integer labels
- **Focal Loss:** Hard examples pe focus — imbalanced data ke liye
- **Hinge Loss:** SVM ke liye

**Regression:**
- **MSE:** Mean Squared Error — large errors penalize zyada
- **MAE:** Mean Absolute Error — outlier robust
- **Huber Loss:** MSE + MAE combination — best of both
- **Log-cosh:** Smooth approximation of Huber

### 2.6 Weight Initialization

**Kyun important hai?**
- Wrong initialization → vanishing/exploding gradients
- Training fail ho sakta hai ya bahut slow ho sakta hai

| Method | Description | Best For |
|--------|-------------|----------|
| **Zero Init** | Sab weights 0 — KABHI nahi karna | Nothing |
| **Random Init** | Small random values | Simple networks |
| **Xavier/Glorot** | Var = 2/(n_in + n_out) | Sigmoid, Tanh |
| **He Init** | Var = 2/n_in | ReLU and variants |
| **Kaiming** | Same as He | PyTorch default for ReLU |

### 2.7 Batch Normalization

**Concept:** Har layer ke output ko normalize karo (mean=0, var=1) before next layer.

**Benefits:**
- Faster training (higher learning rates chalte hain)
- Reduces internal covariate shift
- Mild regularization effect
- Less sensitive to weight initialization

**How it works:**
1. Mini-batch ka mean aur variance calculate karo
2. Normalize karo: x̂ = (x - μ) / √(σ² + ε)
3. Scale aur shift: y = γx̂ + β (learnable parameters)

**Layer Normalization vs Batch Normalization:**
- **BatchNorm:** Batch ke across normalize (batch size pe depend karta hai). CNNs mein.
- **LayerNorm:** Ek sample ke features across normalize. Transformers aur RNNs mein. Batch size se independent.

---

## 3. Convolutional Neural Networks (CNN)

### 3.1 CNN Overview

**Kyun banaya?**
- Fully connected networks high-dimensional images ke liye impractical — too many parameters
- CNN locally connected hai — spatial hierarchy of features seekhta hai

**Key Insight:** Images mein local patterns hote hain (edges, textures, shapes) jo hierarchically combine hote hain

### 3.2 Core Components

**Convolutional Layer:**
- Filter/Kernel (eg. 3×3) image pe slide karta hai
- Dot product se feature map banata hai
- Har filter ek type ka feature detect karta hai (edges, corners, etc.)
- Parameters: kernel_size, stride, padding, number of filters

**Pooling Layer:**
- Feature map ka size reduce karta hai (downsampling)
- **Max Pooling:** Region ka maximum value lo — most common
- **Average Pooling:** Region ka average lo
- **Global Average Pooling:** Pura feature map ka ek average
- Benefits: Translation invariance, computation reduce, overfitting control

**Fully Connected Layer:**
- CNN ke end mein — final classification/regression
- Flatten karke FC layers mein pass karo

### 3.3 Key Concepts

**Stride:** Filter kitna slide ho har step mein (stride=1: har pixel, stride=2: alternate)

**Padding:**
- **Valid:** No padding — output size < input
- **Same:** Padding add karke output = input size maintain karo

**Receptive Field:** Ek neuron kitni input image area "dekh" raha hai. Deeper layers ka receptive field bada hota hai.

**1×1 Convolution:** Channels reduce/increase karna without spatial change — "channel-wise pooling"

**Depthwise Separable Convolution:** Spatial aur channel convolutions ko alag karo — much fewer parameters (MobileNet)

### 3.4 Famous CNN Architectures

| Architecture | Year | Key Innovation |
|-------------|------|----------------|
| **LeNet-5** | 1998 | First successful CNN (digit recognition) |
| **AlexNet** | 2012 | Deep CNN, ReLU, Dropout, GPU training — started DL revolution |
| **VGGNet** | 2014 | Very deep (16/19 layers), 3×3 filters only, simple architecture |
| **GoogLeNet/Inception** | 2014 | Inception module — multiple filter sizes parallel |
| **ResNet** | 2015 | Skip/Residual connections — 152 layers! Solved vanishing gradient |
| **DenseNet** | 2017 | Dense connections — har layer sabhi previous layers se connected |
| **EfficientNet** | 2019 | Compound scaling — width, depth, resolution simultaneously |
| **Vision Transformer (ViT)** | 2020 | Transformer architecture for images |

**ResNet ka importance (MOST ASKED):**
- **Problem:** Very deep networks mein vanishing gradient + degradation problem
- **Solution:** Skip/Residual connections: output = F(x) + x
- Identity shortcut: gradient directly flow kar sakta hai
- 152 layers tak train ho sakta hai
- Har subsequent architecture ne ResNet ki building block use ki

### 3.5 Applications
- Image Classification
- Object Detection (YOLO, Faster R-CNN, SSD)
- Image Segmentation (U-Net, Mask R-CNN)
- Face Recognition (FaceNet, ArcFace)
- Medical Image Analysis
- Autonomous Driving
- Style Transfer

---

## 4. Recurrent Neural Networks (RNN)

### 4.1 RNN Concept

**Kyun chahiye?** Sequential data ke liye — text, time series, audio, video. Order matters!

**How it works:**
- Har time step pe input + previous hidden state → new hidden state + output
- Hidden state = "memory" of what came before
- Same weights shared across all time steps (weight sharing)

**Formula:** hₜ = f(W_hh · hₜ₋₁ + W_xh · xₜ + b)

### 4.2 Problems with Vanilla RNN

**Vanishing Gradient:**
- Long sequences mein gradients multiply hote hue 0 ke paas aa jaate hain
- Model long-term dependencies seekh nahi paata
- Example: "I grew up in India... I speak Hindi" — "India" bahut pehle tha

**Exploding Gradient:**
- Gradients multiply hote hue extremely large ho jaate hain
- Solution: Gradient Clipping (gradient ko max value pe cap karo)

### 4.3 LSTM (Long Short-Term Memory)

**Concept:** Special RNN jo long-term dependencies remember kar sakta hai.

**Three Gates:**
1. **Forget Gate:** Purani information mein se kya bhulna hai decide karta hai
   - f = σ(W_f · [hₜ₋₁, xₜ] + b_f)
   
2. **Input Gate:** Nayi information mein se kya store karna hai decide karta hai
   - i = σ(W_i · [hₜ₋₁, xₜ] + b_i)
   - C̃ = tanh(W_c · [hₜ₋₁, xₜ] + b_c)
   
3. **Output Gate:** Cell state mein se kya output karna hai decide karta hai
   - o = σ(W_o · [hₜ₋₁, xₜ] + b_o)
   - hₜ = o × tanh(Cₜ)

**Cell State (Cₜ):** Information highway — uninterrupted gradient flow — solves vanishing gradient!
- Cₜ = fₜ × Cₜ₋₁ + iₜ × C̃ₜ

### 4.4 GRU (Gated Recurrent Unit)

**LSTM ka simplified version** — 2 gates instead of 3

**Two Gates:**
1. **Reset Gate (r):** Short-term memory control
2. **Update Gate (z):** Long-term memory control (Forget + Input gate combined)

**LSTM vs GRU:**
- GRU simpler hai — fewer parameters, faster training
- LSTM zyada expressive hai — long sequences ke liye better
- Practice mein: comparable performance, GRU try pehle karo

### 4.5 Bidirectional RNN

- Do RNNs — ek forward (left to right), ek backward (right to left)
- Dono directions ki information combine hoti hai
- Use: NLP tasks jahan full context chahiye (Named Entity Recognition, Translation)
- Limitation: Real-time prediction mein use nahi ho sakta (future info chahiye)

### 4.6 Sequence-to-Sequence (Seq2Seq)

- **Encoder:** Input sequence ko fixed-size vector (context) mein compress karo
- **Decoder:** Context vector se output sequence generate karo
- **Use:** Machine Translation, Text Summarization, Chatbots
- **Problem:** Fixed-size context vector = information bottleneck for long sequences
- **Solution:** ATTENTION mechanism!

---

## 5. Transformers & Attention

### 5.1 Attention Mechanism

**Problem:** Seq2Seq mein puri input sequence ek fixed vector mein compress hoti hai — information loss

**Solution:** Decoder ko directly SABHI encoder outputs dekhne do — relevant parts pe zyada "attention" de

**How Attention works:**
1. Decoder ka current state + sabhi encoder states ke beech similarity score calculate karo
2. Scores ko softmax se probabilities mein convert karo (attention weights)
3. Encoder states ka weighted sum = context vector
4. Ye dynamic context vector har decoder step pe different hota hai

**Types:**
- **Additive/Bahdanau Attention:** Neural network se scores compute
- **Multiplicative/Luong Attention:** Dot product se scores compute
- **Self-Attention:** Ek sequence khud apne different parts pe attend kare

### 5.2 Transformer Architecture ("Attention is All You Need" - 2017)

**Revolutionary because:** RNN/LSTM ko completely replace kiya — NO recurrence, sirf attention!

**Key Innovation: Self-Attention** — sequence mein har word sabhi dusre words ko attend karta hai simultaneously

**Architecture:**
```
Input → Embedding + Positional Encoding → 
  ENCODER (Nx):
    → Multi-Head Self-Attention
    → Add & Normalize (Residual Connection)
    → Feed-Forward Network
    → Add & Normalize
  DECODER (Nx):
    → Masked Multi-Head Self-Attention
    → Add & Normalize
    → Multi-Head Cross-Attention (attend to encoder output)
    → Add & Normalize
    → Feed-Forward Network
    → Add & Normalize
→ Linear → Softmax → Output
```

### 5.3 Self-Attention (Scaled Dot-Product)

**Q, K, V (Query, Key, Value):**
- Har word ka teen representations banao: Query, Key, Value
- **Query:** "Main kya dhundh raha hoon?"
- **Key:** "Mere paas kya hai?"
- **Value:** "Meri actual information kya hai?"

**Formula:** Attention(Q,K,V) = softmax(QKᵀ/√dₖ) × V

**Steps:**
1. Q aur K ka dot product → similarity scores
2. √dₖ se divide → scaling for stable gradients
3. Softmax → attention weights (probabilities)
4. Weights × V → weighted output

**Why √dₖ scaling?** Large dot products pe softmax saturate hota hai → vanishing gradients. Scaling se stable rehta hai.

### 5.4 Multi-Head Attention

- Ek single attention ki jagah multiple "heads" use karo
- Har head different representation subspace mein attend karta hai
- Parallel hain — ek head grammar dekhe, dusra semantics, teesra position
- Outputs concatenate karke project karo
- head = 8 ya 16 typical hai

### 5.5 Positional Encoding

**Problem:** Transformer mein koi recurrence nahi — sequence order ka pata nahi chalta
**Solution:** Position information embedding mein add karo

**Sinusoidal Positional Encoding:**
- Even positions: PE(pos,2i) = sin(pos/10000^(2i/d))
- Odd positions: PE(pos,2i+1) = cos(pos/10000^(2i/d))
- Benefits: Extendable to any sequence length, relative positions learn ho sakte hain

**Learned Positional Encoding:** Positions ko bhi learnable parameters banao (BERT, GPT use karte hain)

**RoPE (Rotary Position Embedding):** Modern models (LLaMA, etc.) — relative positions directly attention mein encode

### 5.6 Key Transformer Models

| Model | Type | Pre-training Task | Best For |
|-------|------|-------------------|----------|
| **BERT** | Encoder only | Masked Language Model + NSP | Understanding (classification, NER, QA) |
| **GPT** | Decoder only | Next token prediction (autoregressive) | Generation (text, code, chat) |
| **T5** | Encoder-Decoder | Text-to-text framework | Any NLP task (translate, summarize, QA) |
| **BART** | Encoder-Decoder | Denoising autoencoder | Summarization, Translation |

**BERT (Bidirectional Encoder Representations from Transformers):**
- Bidirectional context — left + right dono dekhta hai
- MLM (Masked Language Modeling): 15% tokens mask karo, predict karo
- NSP (Next Sentence Prediction): Do sentences ka relationship predict karo
- Fine-tuning: Task-specific head lagao (classification, NER, QA)
- Variants: RoBERTa (better training), ALBERT (parameter efficient), DistilBERT (smaller)

**GPT (Generative Pre-trained Transformer):**
- Autoregressive — left to right generate karta hai
- Pre-train on massive text → fine-tune for tasks
- GPT-2 → GPT-3 (175B params) → GPT-4 (multimodal) → GPT-4o
- In-context learning: Few-shot prompting se task solve karo bina fine-tuning ke

---

## 6. Natural Language Processing (NLP)

### 6.1 Text Preprocessing

**Pipeline:**
1. **Tokenization:** Text ko tokens (words/subwords) mein split karo
2. **Lowercasing:** Case normalize karo
3. **Stop words removal:** Common words remove (the, is, at)
4. **Stemming:** Word ko root form mein: running → run (crude, rule-based)
5. **Lemmatization:** Word ko proper base form mein: better → good (uses dictionary)
6. **Punctuation removal**
7. **Special character handling**

### 6.2 Text Representation

| Method | Description | Limitation |
|--------|-------------|------------|
| **Bag of Words (BoW)** | Word counts ka vector | Word order lost, sparse |
| **TF-IDF** | Term frequency × inverse document frequency | Order lost, but weighted |
| **Word2Vec** | Dense word embeddings (CBOW/Skip-gram) | One vector per word, no context |
| **GloVe** | Global co-occurrence matrix + embeddings | Static embeddings |
| **FastText** | Subword embeddings (character n-grams) | Handles unknown words |
| **ELMo** | Contextualized embeddings (BiLSTM) | Slow, separate feature |
| **BERT Embeddings** | Deep contextualized (Transformer) | Heavy compute |

**Word2Vec detail:**
- **CBOW:** Context words se center word predict karo
- **Skip-gram:** Center word se context words predict karo
- Similar words ka vector close hota hai: King - Man + Woman ≈ Queen

**TF-IDF:**
- TF = (word count in doc) / (total words in doc)
- IDF = log(total docs / docs containing word)
- TF-IDF = TF × IDF
- Rare but important words ko high weight deta hai

### 6.3 Modern Tokenization

| Method | Description | Example |
|--------|-------------|---------|
| **BPE (Byte Pair Encoding)** | Frequent character pairs merge karke vocabulary build | GPT uses this |
| **WordPiece** | BPE jaisa but likelihood-based | BERT uses this |
| **SentencePiece** | Language-agnostic, raw text se tokenize | T5, LLaMA |
| **Unigram** | Probability-based subword selection | SentencePiece variant |

### 6.4 NLP Tasks

| Task | Description | Example Models |
|------|-------------|----------------|
| **Text Classification** | Category assign karo | BERT, DistilBERT |
| **Named Entity Recognition** | Entities identify karo (person, org, location) | SpaCy, BERT-NER |
| **Sentiment Analysis** | Positive/Negative classify karo | Fine-tuned BERT |
| **Machine Translation** | Language translate karo | T5, mBART, NLLB |
| **Text Summarization** | Summary generate karo | BART, Pegasus, T5 |
| **Question Answering** | Question ka answer find karo | BERT, DPR |
| **Text Generation** | New text generate karo | GPT, LLaMA |
| **Semantic Similarity** | Do texts kitne similar hain | Sentence-BERT |

---

## 7. Generative AI

### 7.1 Large Language Models (LLMs)

**What are LLMs?**
- Billions of parameters wale transformer models
- Massive text data pe pre-trained
- Next token prediction se language understanding aur generation

**Key Models:**

| Model | Organization | Parameters | Key Feature |
|-------|-------------|------------|-------------|
| GPT-4 | OpenAI | ~1.8T (rumored) | Multimodal, RLHF |
| Claude | Anthropic | - | Constitutional AI, long context |
| LLaMA 3 | Meta | 8B-405B | Open-source |
| Gemini | Google | - | Multimodal, long context |
| Mistral | Mistral AI | 7B-8x22B | Efficient MoE |

### 7.2 Training LLMs

**Pre-training:**
- Next token prediction on massive corpus
- Self-supervised — labels data se khud generate
- Compute: Thousands of GPUs, weeks/months

**Fine-tuning:**
- Pre-trained model ko specific task/domain pe adapt karo
- Supervised Fine-Tuning (SFT): Labeled data pe train
- RLHF (Reinforcement Learning from Human Feedback):
  1. SFT model train karo
  2. Human preferences collect karo
  3. Reward model train karo
  4. PPO se model optimize karo

**Parameter-Efficient Fine-Tuning (PEFT):**
- **LoRA (Low-Rank Adaptation):** Weight matrices ko low-rank decomposition se fine-tune. Original weights freeze, small trainable matrices add.
- **QLoRA:** LoRA + quantization = less memory
- **Prefix Tuning:** Learnable prefixes add karo
- **Adapter Layers:** Small trainable layers insert karo between frozen layers

### 7.3 Prompt Engineering

**Techniques:**
- **Zero-shot:** Direct question without examples
- **Few-shot:** Kuch examples provide karke task explain karo
- **Chain-of-Thought (CoT):** "Think step by step" — reasoning improve
- **Tree-of-Thought:** Multiple reasoning paths explore
- **ReAct:** Reasoning + Action — tools use karke answer
- **System Prompts:** Model behavior define karo
- **Role Prompting:** "You are an expert..." format

### 7.4 Retrieval Augmented Generation (RAG)

**Problem:** LLMs ka knowledge cutoff hota hai, hallucinate karte hain

**Solution:** External knowledge base se relevant documents retrieve karke context mein provide karo

**RAG Pipeline:**
1. **Indexing:** Documents chunk karo → embeddings generate → vector DB mein store
2. **Retrieval:** User query ka embedding → vector DB mein similarity search → top-K relevant chunks
3. **Generation:** Retrieved chunks + user query → LLM → grounded answer

**Vector Databases:** Pinecone, Weaviate, Chroma, Milvus, FAISS, Qdrant

**Chunking Strategies:**
- Fixed-size chunks (e.g., 512 tokens)
- Sentence-based chunking
- Semantic chunking
- Recursive character splitting

### 7.5 Generative Models (Image/Video)

**GANs (Generative Adversarial Networks):**
- Generator: Realistic data generate kare
- Discriminator: Real vs fake distinguish kare
- Dono compete karte hain → Generator improve hota hai
- Types: DCGAN, StyleGAN, CycleGAN, Pix2Pix
- Problems: Mode collapse, training instability

**VAE (Variational Autoencoders):**
- Encoder: Data → latent space (mean + variance)
- Decoder: Latent space → data reconstruct
- Regularized: Latent space smooth aur continuous
- Sampling se new data generate

**Diffusion Models:**
- Forward: Image mein gradually noise add karo (T steps)
- Reverse: Noise se gradually image reconstruct karo
- Trained to denoise at each step
- State-of-art image generation (DALL-E, Stable Diffusion, Midjourney)
- Better than GANs: Stable training, diverse outputs, no mode collapse

### 7.6 AI Agents

**Concept:** LLMs + Tools + Memory + Planning

**Components:**
- **Brain:** LLM for reasoning
- **Tools:** Code execution, web search, APIs
- **Memory:** Short-term (conversation) + Long-term (persistent)
- **Planning:** Task decomposition, reflection

**Frameworks:** LangChain, CrewAI, AutoGPT, LangGraph

---

## 8. Computer Vision

### 8.1 Tasks

| Task | Description | Output |
|------|-------------|--------|
| **Classification** | Puri image ka ek label | "Cat" |
| **Object Detection** | Objects locate karo + classify | Bounding boxes + labels |
| **Segmentation** | Pixel level classification | Pixel-wise mask |
| **Instance Segmentation** | Har object instance alag segment | Individual masks |
| **Pose Estimation** | Body keypoints detect karo | Skeleton visualization |
| **Image Generation** | Naye images create karo | New image |

### 8.2 Object Detection

**Two-stage Detectors (Accurate but slow):**
- R-CNN → Fast R-CNN → Faster R-CNN → Mask R-CNN
- Region proposal + classification alag

**One-stage Detectors (Fast):**
- **YOLO (You Only Look Once):** Image ko grid mein divide, simultaneously detect + classify. Real-time! YOLOv1 → v8 → YOLO11
- **SSD (Single Shot Detector):** Multi-scale feature maps pe detect
- **RetinaNet:** Focal Loss se class imbalance solve

**Anchor-free Detectors:**
- CenterNet, FCOS — predefined anchors nahi, direct prediction

### 8.3 Image Segmentation

- **Semantic Segmentation:** Har pixel ko class assign (U-Net, DeepLab, FCN)
- **Instance Segmentation:** Har object instance alag (Mask R-CNN)
- **Panoptic Segmentation:** Semantic + Instance combined

**U-Net (Medical Imaging ke king):**
- Encoder (downsampling) + Decoder (upsampling)
- Skip connections — encoder ke features directly decoder ko
- Less data mein bhi achha perform karta hai

### 8.4 Vision Transformers (ViT)

- Image ko patches mein divide karo (16×16)
- Har patch ko embedding mein convert
- Transformer encoder mein feed karo
- Classification token se predict
- Large data pe CNN se better, small data pe CNN still better
- DINO, DINOv2: Self-supervised ViT training

---

## 9. Reinforcement Learning

### 9.1 Core Concepts

| Term | Meaning |
|------|---------|
| **Agent** | Learner / decision maker |
| **Environment** | World jisme agent interact karta hai |
| **State (s)** | Current situation |
| **Action (a)** | Agent ka decision |
| **Reward (r)** | Action ka feedback (+ ya -) |
| **Policy (π)** | State se action ka mapping strategy |
| **Value Function V(s)** | State se expected total future reward |
| **Q-Function Q(s,a)** | State-action pair se expected total future reward |
| **Discount Factor (γ)** | Future rewards ki importance (0-1) |

### 9.2 Key Algorithms

**Model-Free:**
- **Q-Learning:** Q-table update karo iteratively. Off-policy.
- **SARSA:** On-policy Q-learning variant
- **Deep Q-Network (DQN):** Q-table ki jagah neural network. Atari games!
- **Policy Gradient (REINFORCE):** Directly policy optimize karo
- **Actor-Critic:** Actor (policy) + Critic (value function) dono train
- **PPO (Proximal Policy Optimization):** Stable policy updates, RLHF mein use hota hai
- **SAC (Soft Actor-Critic):** Entropy bonus for exploration

**Model-Based:**
- Environment ka model learn karo, phir plan karo
- AlphaGo, MuZero

### 9.3 Exploration vs Exploitation
- **Exploration:** Naye actions try karo (knowledge gain)
- **Exploitation:** Known best action karo (reward maximize)
- **ε-greedy:** ε probability se random, 1-ε se best action
- **UCB (Upper Confidence Bound):** Uncertainty consider karke explore
- **Thompson Sampling:** Bayesian approach

### 9.4 Applications
- Game AI (AlphaGo, Atari, Dota2)
- Robotics (manipulation, locomotion)
- RLHF for LLMs (ChatGPT, Claude)
- Autonomous driving
- Recommendation systems
- Resource allocation
- Trading strategies

---

## 10. MLOps & AI in Production

### 10.1 MLOps Lifecycle
```
Data Management → Experiment Tracking → Model Training →
Model Evaluation → Model Registry → Model Deployment →
Monitoring → Retraining
```

### 10.2 Key Concepts

**Experiment Tracking:**
- Hyperparameters, metrics, artifacts log karo
- Tools: MLflow, Weights & Biases, Neptune

**Model Registry:**
- Model versions manage karo
- Staging → Production → Archived lifecycle
- Model lineage track karo

**CI/CD for ML:**
- Continuous Integration: Code + data + model tests
- Continuous Delivery: Automated model deployment
- Continuous Training: Data change pe automatic retrain

**Feature Store:**
- Centralized feature management
- Consistent features training + serving mein
- Tools: Feast, Tecton

### 10.3 Model Serving

**Patterns:**
- **Batch:** Periodic predictions (nightly reports)
- **Real-time:** API-based instant predictions
- **Streaming:** Continuous predictions (Kafka + model)
- **Edge:** Mobile/IoT device pe model

**Model Optimization for Serving:**
- **Quantization:** Float32 → Int8/Float16 → smaller, faster
- **Pruning:** Unnecessary weights remove karo → smaller model
- **Distillation:** Large model (teacher) se small model (student) train karo
- **ONNX:** Framework-agnostic model format

### 10.4 Monitoring

**What to Monitor:**
- **Model Performance:** Accuracy, latency, throughput
- **Data Quality:** Missing values, schema changes, anomalies
- **Data Drift:** Input distribution change — PSI, KS test
- **Concept Drift:** Input-output relationship change
- **Resource Usage:** GPU/CPU/Memory utilization

### 10.5 Responsible AI in Production
- Fairness metrics monitor karo
- Model cards maintain karo (documentation)
- Audit trails rakho
- Human-in-the-loop for critical decisions
- Adversarial testing karo

---

## 11. Interview Questions & Answers

### Q1: Vanishing and Exploding Gradient problem explain karein.
**Answer:**
- **Vanishing:** Deep networks mein backpropagation ke time gradients multiply hote hue 0 ke paas aa jaate hain. Sigmoid/Tanh mein ye problem zyada hoti hai. Result: Early layers train nahi hote.
- **Exploding:** Gradients multiply hote hue extremely large ho jaate hain. Result: Weights NaN ho jaate hain.
- **Solutions:** ReLU activation, skip connections (ResNet), batch normalization, LSTM/GRU (for RNN), gradient clipping (exploding ke liye), proper weight initialization (He/Xavier).

### Q2: Transformer mein Self-Attention kaise kaam karta hai?
**Answer:**
- Har token ka Query, Key, Value vector banao
- Q aur K ka dot product → similarity scores
- √dₖ se divide → scaling
- Softmax → attention weights
- Weights × V → context-aware output
- Multi-head: Multiple attention heads parallel different aspects dekhte hain
- Benefit: Puri sequence ek saath process, koi recurrence nahi, parallelizable

### Q3: BERT vs GPT ka difference?
**Answer:**
- **BERT:** Encoder-only, bidirectional, MLM training, understanding tasks (classification, NER, QA)
- **GPT:** Decoder-only, autoregressive (left-to-right), next token prediction, generation tasks (text, code, chat)
- **BERT** understanding mein better, **GPT** generation mein better
- BERT ko fine-tune karna padta hai, GPT few-shot/zero-shot mein kaam kar sakta hai (large scale pe)

### Q4: CNN mein Receptive Field kya hai?
**Answer:**
- Ek neuron input image ka kitna area "dekh" sakta hai
- Deeper layers ka receptive field bada hota hai
- Stacking 3×3 conv layers se efficiently receptive field badhta hai
- Pooling/striding se bhi badhta hai
- Important kyunki model ko global context chahiye classification ke liye

### Q5: Dropout kaise kaam karta hai aur kyun effective hai?
**Answer:**
- Training mein randomly p% neurons ko zero kar deta hai (typically 0.5)
- Har forward pass mein different sub-network train hota hai
- Ensemble effect: Actually many sub-networks train ho rahi hain
- Co-adaptation prevent karta hai — neurons independent features seekhte hain
- Inference time: Dropout band, weights ko (1-p) se scale
- Test pe: Sabhi neurons active hain, expected output same rahe

### Q6: Batch Normalization kyun kaam karta hai?
**Answer:**
- Internal covariate shift reduce — har layer ka input distribution stable
- Higher learning rates use kar sakte hain → faster training
- Mild regularization effect (batch statistics noisy hain)
- Reduces dependency on weight initialization
- Smoother loss landscape → easier optimization
- Limitation: Batch size pe depend karta hai, small batch mein noisy statistics

### Q7: ResNet ki skip connections kyun important hain?
**Answer:**
- Gradient ko directly deep layers tak flow hone dete hain (vanishing gradient solve)
- Identity mapping learn karna easy hai — worst case mein layers skip ho jaate hain
- Deeper networks ko effectively train kar sakte hain (152+ layers)
- Degradation problem solve — deeper network shallow se bura nahi perform karega
- Ensemble effect — different depth ke paths simultaneously train hote hain

### Q8: LSTM mein Forget Gate ka role kya hai?
**Answer:**
- Cell state mein se irrelevant information discard karta hai
- Sigmoid output (0-1): 0 = completely forget, 1 = completely remember
- Previous hidden state + current input se decision leta hai
- Example: Sentence mein subject change ho jaye toh purani gender info forget karo
- Ye long-term dependency ka key mechanism hai — kya remember karna hai, kya bhulna hai

### Q9: GANs mein Mode Collapse kya hai?
**Answer:**
- Generator sirf limited types ki output generate kare, diversity lose kare
- Example: MNIST pe sirf "1" generate kare, baaki digits nahi
- Discriminator agar bahut strong ho jaye toh generator ek "safe" output pe stuck ho jaata hai
- Solutions: Wasserstein GANs, progressive growing, spectral normalization, mini-batch discrimination, feature matching

### Q10: Transfer Learning kyun effective hai?
**Answer:**
- Lower layers generic features seekhti hain (edges, textures, shapes) jo sabhi tasks mein useful hain
- Higher layers task-specific features seekhti hain
- Pre-trained model ka knowledge new task pe leverage
- Kam data mein bhi accha performance (fine-tune last few layers)
- Faster convergence — scratch se train karne ki zaroorat nahi
- ImageNet pre-trained models almost har vision task ke liye starting point

### Q11: Attention mechanism RNN se better kyun hai?
**Answer:**
- **Parallelization:** Attention fully parallel, RNN sequential
- **Long-range dependencies:** Direct connections (vs RNN mein information decay)
- **Constant path length:** Koi bhi do positions ke beech O(1) path
- **Interpretability:** Attention weights se pata chalta hai model kahan dekh raha
- **Scalability:** Much larger models train ho sakte hain

### Q12: RAG (Retrieval Augmented Generation) explain karein.
**Answer:**
- LLMs hallucinate karte hain aur knowledge cutoff hota hai
- RAG: External knowledge base se relevant information retrieve karke LLM ko context mein do
- Pipeline: Query → Embedding → Vector DB search → Top-K chunks → LLM prompt mein inject → Grounded answer
- Benefits: Up-to-date info, less hallucination, source citations, no retraining needed
- Components: Embedding model, vector store, retriever, LLM, chunking strategy

### Q13: Diffusion Models kaise kaam karte hain?
**Answer:**
- Forward process: Clean image mein gradually Gaussian noise add (T steps)
- Reverse process: Neural network noise predict kare aur remove kare step by step
- Training: Random timestep pe noise predict karna seekho
- Inference: Pure noise se start → iteratively denoise → clean image
- Classifier-free guidance: Conditional + unconditional output ka blend
- Better than GANs: Stable training, diverse outputs, no mode collapse

### Q14: RLHF kya hai aur LLMs mein kaise use hota hai?
**Answer:**
- Reinforcement Learning from Human Feedback
- Step 1: SFT — Model ko demonstrations pe fine-tune
- Step 2: Reward Model — Human preferences se reward model train
- Step 3: PPO — Reward model use karke LLM optimize
- Purpose: Helpful, harmless, honest responses generate karna
- GPT-4, Claude, Gemini sab RLHF use karte hain
- Alternative: DPO (Direct Preference Optimization) — reward model skip

### Q15: Model ko production mein deploy karne ke challenges kya hain?
**Answer:**
- **Latency:** Real-time predictions ke liye low latency chahiye
- **Scalability:** Traffic spikes handle karnna
- **Data drift:** Model performance degrade over time
- **Monitoring:** Performance, data quality, drift continuously track
- **Versioning:** Model, data, code sab version control
- **A/B testing:** New model safely roll out
- **Resource management:** GPU/memory optimization
- **Security:** Model theft, adversarial attacks, data privacy

### Q16: What is Knowledge Distillation?
**Answer:**
- Large model (Teacher) se small model (Student) train karo
- Student teacher ki "soft labels" se seekhta hai (probability distribution)
- Soft labels mein inter-class relationships ki information hoti hai
- Temperature parameter: Softmax ko softer banata hai → richer information
- Result: Small model large jaisa perform kare but faster/cheaper
- Example: DistilBERT (BERT ka 60% size, 97% performance)

### Q17: What are embeddings and why are they important?
**Answer:**
- Dense, low-dimensional vector representations of discrete objects (words, images, users)
- Capture semantic meaning — similar items ke vectors close
- Vs one-hot: Sparse, high-dimensional, no semantic info
- Use: NLP (word2vec, BERT), recommendations (user/item embeddings), search (query/doc embeddings)
- Embedding space mein arithmetic: King - Man + Woman ≈ Queen
- Foundation of modern AI — RAG, similarity search, clustering

### Q18: Explain the concept of few-shot, zero-shot, and one-shot learning.
**Answer:**
- **Zero-shot:** Koi example nahi, sirf task description se predict
- **One-shot:** Ek example dekhke seekh le
- **Few-shot:** 2-5 examples se seekh le
- LLMs mein: In-context learning — prompt mein examples do, model pattern samjh le
- Vision: Siamese Networks, CLIP (image-text alignment)
- Important kyunki large labeled data hamesha available nahi hota

### Q19: What is the difference between Semantic Search and Keyword Search?
**Answer:**
- **Keyword:** Exact word match, BM25/TF-IDF based. "car" search karo toh "automobile" nahi milega
- **Semantic:** Meaning samajhke search, embedding-based. "car" se "automobile" bhi milega
- **Hybrid:** Dono combine — keyword precision + semantic understanding
- Semantic search ke liye: Text → embedding → vector similarity (cosine)
- Applications: RAG retrieval, product search, document search

### Q20: Explain Model Quantization.
**Answer:**
- Model ke weights ko lower precision mein convert karna
- Float32 → Float16 (half precision) → Int8 → Int4
- **Benefits:** Smaller model size, faster inference, less memory
- **Tradeoff:** Slight accuracy loss (minimal if done right)
- **Types:** Post-training quantization (PTQ), Quantization-aware training (QAT)
- **GPTQ, AWQ, GGUF:** Popular LLM quantization methods
- Example: 70B model Float16 mein ~140GB, Int4 mein ~35GB

---

## Quick Revision Table

| Topic | One-line Summary |
|-------|-----------------|
| Neural Network | Layers of neurons with weights, forward + backprop |
| CNN | Convolution + Pooling — spatial feature extraction |
| RNN/LSTM | Sequential data + memory (gates control information flow) |
| Transformer | Self-attention, no recurrence, parallelizable |
| BERT | Encoder, bidirectional, understanding tasks |
| GPT | Decoder, autoregressive, generation tasks |
| Attention | Focus on relevant parts dynamically |
| GAN | Generator vs Discriminator competition |
| Diffusion | Noise add → learn to denoise → generate |
| RL | Agent learns by reward/punishment in environment |
| RAG | Retrieve relevant docs + LLM generate answer |
| RLHF | Human preferences se LLM align |
| LoRA | Efficient fine-tuning with low-rank matrices |
| Quantization | Lower precision = faster + smaller model |
| Distillation | Large teacher → small student model |

---

*10+ Years Experience Level - AI & Deep Learning Theory*
