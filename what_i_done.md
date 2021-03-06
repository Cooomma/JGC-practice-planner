# JGC修行飛行計劃模擬器



## 關於JGC的小小說明

在開始說JGC之前，首先需要知道飛行常客計劃(FFP)究竟是什麼一回事。

基本上所有的傳統航空公司都會設有飛行常客計劃來獎勵/回饋經常乘搭的乘客。比較早期的飛行常客計劃會用航段+飛行里數來決定會員等級。後來玩法一直演化，現在比較常看到的是會員積分和飛行里數。

`會員積分` 是必須通過實際的飛行來累積。而不同的Booking Class對應的會員積分會有不一樣。

`飛行里數` 獲取的途徑就多很多了，常見的有 信用卡、酒店、租車累積。

如果要求說每年可以換取免費機票去玩的話，基本上下文就與你沒太大關係了。JGC修行這個東西是在修會員積分。

### 什麼是JGC

JGC = JAL Global Club 是屬於日本航空的飛行常客計劃的其中一個分支。當你擁有的時候，首先它是日本航空的高級會員的象徵，然後因為日本航空是屬於寰宇一家(OneWorld)的成員，所以對應的會籍也會等於對應寰宇一家的會籍。詳細的說明就如下圖的官方說明：



![JGC Level](https://www.jal.co.jp/en/jalmile/flyon/commonY16/img/txt_status_001Y15_01.jpg)



### 入手方式

就是飛吧...不管你用什麼方法，目標就是`在一個自然年裡，把會員帳號裡的FOP餘額提升到50000`

所以，這就是一條不停在坐飛機的修行之路



詳細JGC介紹：[JGC 大解析：新手必讀的 JGC 修行攻略 – 如何累積 FOP](<http://d3consulting.org/what-is-jgc/>)



## 寫一個模擬器幹嘛

就是無聊找事做。

基本上一直以來，自己寫程式都是靠直覺來寫的。對於Algorithm, Data Sturcture也是靠直覺...這次就當作是一道練習題吧

另外，羽田-沖繩航線都是被當作JGC修行首選之路。當然我絕對相信群眾的智慧，只是既然是無聊，那就寫來玩玩看。

###  

## 模擬器在幹嘛

就算在算飛行計劃啊。



### 核心問題

`如何在有限的時間內 選擇最多點數的航班 然後累積到達50000`



### 基本邏輯

JGC的規則不是很多：

1. 對於非日本人，在飛日本國內航線的時候， FOP都會有2倍的加成。
2. 如果通過JAL Explorer Pass都會有100%里程數
3. 盡可能飛
4. FOP計算公式: `Sector Milage * Multiplier + Bonus`

基本常理：

1. 轉機時間要充分：我預計是30分鐘
2. 國內航班沒有跨日的
3. 前一天到達的城市是下一天出發的城市
4. 進入日本和離開日本要在同一個城市(其實不同城市也可以，只要國際線是用Open Jaw就好)



### 資料準備

把這三個東西準備好(Code裡面 `data/`裡面的東西就是上面全部了)，就可以開始寫了



#### [Route(航班)](<https://www.flightradar24.com/data/airlines/jl-jal/routes>)

去Flightradar24先查一下日本航空及子公司總共有那些航班。然後被對應的國內線全都弄下來。



#### [Airports](<https://aviation-edge.com/aviation-api-list/>)

雖然說拉航班的時候會有把航班對應的出發機場和到達機場都會有，但在拉航班的前還是有一份總表比較好做。



#### [Fly-On-Point對照表](<https://www.jal.co.jp/en/jalmile/jdsmt.html>)

官方網站有提供，手動拉下來就好了



## 模擬器究竟怎麼算

### 邏輯(暴力法)

就是一個路線選擇題，當我在機場出發的時候，需要參考現在的時間，選擇在最短的轉機時間裡可以去地方。假設如果HND可以出發去KIX, CTS, OKA，在第一次飛行之後，就會延展出3個平行時空。然後對於這3個平行時空，在參考在下飛機的時間，繼續選擇下一班飛機，直到機場沒有航班 或者 當天已經結束。

因為整個修行不會只有一天，而且第二天出發地點和第一天到達地點會是同一個地方(飛完一整天之後不會再有力氣坐車去第二個城市開始飛第二天的吧? 如果有，服氣！)， 所以假設第二天開始的時間和第一天一樣，從第二天的地方作為起始的機場，繼續重複第一天的事情。

直到最後一天或者k-1天，因為離開日本的航班需要和第一天的航班一樣，所以最後一天的航班的總點必須要和第一天的起始點一致。



### 簡化後的邏輯(稍微簡單的暴力法)

#### Route的最佳化

對於任意一個機場，都一定會有它的航線圖。所以在最早的時候把所有的機場的航線就建立一個Graph. 每次在一個機場的時候只需要過濾這個機場的航班，留下這個機場裡在到達時間之後航班作為選擇。

對於每一條Route的選擇，對於同樣的目的地，只會選擇在允許轉機世界內等候時間最短的航班。因為修行時是不允許在陸地上發呆的。

另外對於隨著修行的天數的推移，之後的天數很有可能出現 之前作為出發點的機場的計劃(Flight Plan), 所以可以建立一個Dict/Map 來存這個作為這個城市作為起始點的所有Flight Plan. 在後面的運算就不用重複模擬了



#### FOP的選擇（敗者有可能復活嗎?)

假設如果第一天的出發點和第一天的結束點是一樣，那這個機場的所有Flight Plan當中 最高的FOP的Flight Plan一定會是重複出現在之後的天數。如果想要減少運算量，可以在這個位置就採取Drop Out的策略。因為死者蘇生是不存在的。但模擬為了模擬所有結果，這裏沒有選擇Drop out.



## 模擬器的結果

`連續飛 HND -> ISG -> HND -> ISG -> HND 四天` `FOP = 45568`加上TSA<->HND國際線的`6786` > JGC所需要的`50000`了



### 為什麼不是羽田沖繩來回?

模擬器目前的計算，只是根據Route來計算，還沒有考慮航班的實際開票成本及難度(有位子才可以飛吧?) JAL Explorer Press的限制。如果單是計算羽田沖繩來回的FOP總值`9472` (Rank: 8) 比 羽田石垣來回的 `11392`(Rank: 1)要低不少



## 模擬器還可以做...



### 最低成本法的修行

以前(2018年)之前的話，可以接上QPX的API來獲取航班價格的資料。但是，2010年Google收購了QPX(ITA Matrix的公司)，而且在2018年4月10號正式將[QPX Express API停用](<https://developers.google.com/qpx-express/>)。 目前可以用的應該只是Skyscanner的QuoteAPI，但Skyscanner被Ctrip收購後，所有的API都要申請。除非用Selium來爬吧



### 修行航班的Delay機率

在Flightradar24的資料當中，如果你是FR24的付費用戶，可以獲得所有航班過去一段時間(取決於帳號等級)內的飛行紀錄。假設如果拿到航班過去365日的資料，應該可以推算出平均航班Delay的時間。從而思考轉機的風險。











