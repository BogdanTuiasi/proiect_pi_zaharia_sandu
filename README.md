# Traducere automată a textului în timp real în realitate augumentată

Acest proiect are ca scop traducerea textului vizibil în realitate augmentată într-o limbă țintă.

La nivel hardware este folosit un dispozitiv **Meta Quest 3** care execută `clientul` și un **calculator** pentru execuția programului `server`.

## Arhitectura proiectului

<table cellpadding="6" width="100%">
  <tr>
    <td width="33%" align="center">
      <img src="documentation/diagrams/main.png" alt="Arhitectura generala" width="100%">
    </td>
    <td width="67%" align="center">
      <img src="documentation/diagrams/client.png" alt="Arhitectura clientului" width="100%">
    </td>
  </tr>
</table>

<table cellpadding="6" width="100%">
  <tr>
    <td align="center">
      <img src="documentation/diagrams/server.png" alt="Arhitectura serverului" width="100%">
    </td>
  </tr>
</table>

<table cellpadding="6" width="100%">
  <tr>
    <td width="55%" align="center">
      <img src="documentation/diagrams/communication.png" alt="Comunicarea dintre client si server" width="100%">
    </td>
    <td width="45%" align="center">
      <img src="documentation/diagrams/optional.png" alt="Module optionale" width="100%">
    </td>
  </tr>
</table>

Clientul (realizat cu Unity în C#) codifică și trimite câmpul vizual al ochelarilor către server, împreună cu alte date necesare configurării sistemului și procesării spațio-temporale. 

Ulterior, preia de la server și decodifică imaginile procesate și trimise spre afișare.

Serverul (scris în Python) preia câmpul vizual al dispozitivului, înlocuiește segmentele de text observate cu segmente de text traduse, iar apoi codifică și trimite rezultatul spre afișare către client.

Comunicarea se realizează printr-o conexiune **TCP**, inițiată de client către adresa IP a calculatorului, pe portul **5000**. Imaginile sunt codificate în format **JPEG**, iar fiecare imagine este precedată de un antet de 4 octeți care indică dimensiunea datelor transmise. Clientul trimite un cadru și așteaptă rezultatul procesării înainte de a trimite următorul cadru, folosind aceeași conexiune pentru ambele sensuri de comunicare.

Procesarea efectivă a imaginilor se realizează printr-un pipeline format din 6 module:

1. Text Detection: efectuează transformări de bază aspura imaginii (precum corecția orientării), detectează zonele cu text și cuprinde fiecare secțiune cu poligoane, luând în calcul detecțiile incerte.

2. Text Tracking: identifică și urmărește în timp fiecare regiune, iar la pierderea sau modificarea radicală a unei regiuni cere recalcularea cu un pipeline complet de OCR.

3. Adaptive Preprocessing: estimează indicatori de calitate a imaginii (ex. contrastul, iluminarea) și aplică transformări de preprocesare potrivite pentru situație.

4. OCR: se fac posibile corecții de perspectivă, iar apoi textul se recunoaște de-a lungul unui interval de timp pentru a reduce erorile.

5. Language Detection + Translation: estimează limba sursă a textului și salvează traducerea în limba țintă la nivel de obiect.

6. Translation Painting: generează și aplică un overlay peste imaginea inițială cu textul tradus, în funcție de condițiile originale.

## Studiu asupra literaturii de specialitate și ale soluțiilor existente

Tabelul următor prezintă lucrări și proiecte relevante pentru recunoașterea optică a caracterelor, procesarea video și urmărirea obiectelor în realitate mixtă.

<table>
  <thead>
    <tr>
      <th>Nr.</th>
      <th>Autor(i) / An</th>
      <th>Titlul articolului / proiectului</th>
      <th>Aplicație / Domeniu</th>
      <th>Tehnologii utilizate</th>
      <th>Metodologie / Abordare</th>
      <th>Rezultate</th>
      <th>Limitări</th>
      <th>Comentarii suplimentare</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>Pankaj Tripathi / 2025</td>
      <td>
        <strong>Text recognition algorithms: 10 methods behind modern OCR</strong>
      </td>
      <td>
        <p>Recunoașterea optică a caracterelor (OCR).</p>
        <p>Digitizarea documentelor.</p>
        <p>Detectarea textului în imagini naturale.</p>
        <p>Recunoașterea scrisului de mână.</p>
      </td>
      <td>
        <p>CTPN, EAST, CRAFT, DBNet.</p>
        <p>CRNN, CTC, TrOCR, PARSeq.</p>
        <p>Word Beam Search, LayoutLMv3 și Donut.</p>
      </td>
      <td>
        <p>Preprocesarea imaginii.</p>
        <p>Detectarea regiunilor de text.</p>
        <p>Recunoașterea caracterelor și decodarea rezultatelor.</p>
        <p>
          Sunt comparate principiile de funcționare, avantajele,
          dezavantajele și scenariile de utilizare ale metodelor.
        </p>
      </td>
      <td>
        <p>EAST este potrivit pentru detecție rapidă.</p>
        <p>CRAFT este potrivit pentru text neregulat.</p>
        <p>CRNN + CTC permite recunoașterea secvențelor de caractere.</p>
        <p>Modelele Transformer precum TrOCR pot gestiona scrisul de mână.</p>
      </td>
      <td>
        <p>
          Performanța reală depinde de calitatea imaginilor,
          limbă, font, orientare, complexitatea fundalului
          și datele de antrenare.
        </p>
      </td>
      <td>
        <p>Character Error Rate (CER).</p>
        <p>Word Error Rate (WER).</p>
        <p>Precizia detecției.</p>
        <p>Timpul de procesare și memoria utilizată.</p>
      </td>
    </tr>
    <tr>
      <td>2</td>
      <td>RapidAI Team</td>
      <td><strong>RapidOCR</strong></td>
      <td>
        <p>
          Recunoașterea optică a textului (OCR) din imagini
          și documente, inclusiv în engleză și chineză.
        </p>
      </td>
      <td>
        <p>Python.</p>
        <p>ONNX Runtime.</p>
        <p>OpenCV.</p>
        <p>Modele PaddleOCR (PP-OCR).</p>
      </td>
      <td>
        <p>
          Utilizează modele preantrenate pentru detecția
          și recunoașterea textului, optimizate pentru inferență
          pe CPU prin ONNX Runtime.
        </p>
        <p>Extrage textul, coordonatele și scorurile de încredere.</p>
      </td>
      <td>
        <p>
          Permite recunoașterea textului fără GPU dedicat,
          cu modele compacte și integrare relativ simplă
          în aplicații backend.
        </p>
      </td>
      <td>
        <p>
          Performanța depinde de calitatea imaginii, rezoluție,
          orientarea textului și modelul utilizat.
        </p>
        <p>
          Nu include implicit traducerea sau înlocuirea
          textului în imagine.
        </p>
      </td>
      <td>
        <p>
          Proiect open-source, fără articol științific propriu
          peer-reviewed identificat.
        </p>
        <p>
          Se bazează pe cercetările PaddleOCR,
          în special PP-OCR (Du et al., 2020).
        </p>
      </td>
    </tr>
    <tr>
      <td>3</td>
      <td>Yuning Du et al. / 2020</td>
      <td><strong>PP-OCR: A Practical Ultra Lightweight OCR System</strong></td>
      <td>
        <p>
          Recunoașterea optică a textului (OCR) din imagini,
          în special în engleză și chineză, pentru aplicații
          cu resurse computaționale limitate.
        </p>
      </td>
      <td>
        <p>PaddlePaddle.</p>
        <p>Deep Learning și CNN.</p>
        <p>Modele lightweight pentru detecția și recunoașterea textului.</p>
      </td>
      <td>
        <p>Detecția textului.</p>
        <p>Clasificarea orientării.</p>
        <p>Recunoașterea caracterelor.</p>
        <p>
          Utilizează tehnici de optimizare și compresie
          a modelelor pentru reducerea dimensiunii
          și îmbunătățirea acurateței.
        </p>
      </td>
      <td>
        <p>
          Sistem OCR ultra-lightweight, cu modele de doar
          3,5 MB pentru 6.622 caractere chinezești și 2,8 MB
          pentru 63 simboluri alfanumerice.
        </p>
        <p>
          Modele preantrenate open-source, validate experimental
          și pentru alte limbi.
        </p>
      </td>
      <td>
        <p>Nu realizează traducerea sau înlocuirea textului în imagine.</p>
        <p>
          Performanța poate fi afectată de imagini neclare,
          text foarte mic și fundaluri complexe.
        </p>
        <p>
          Aceste limitări sunt relevante practic, dar nu sunt
          cuantificate în rezumatul articolului.
        </p>
      </td>
      <td>
        <p>
          Lucrare științifică disponibilă pe arXiv,
          care constituie fundamentul tehnologic al modelelor
          PP-OCR utilizate și de RapidOCR.
        </p>
        <p>Codul și modelele sunt open-source.</p>
      </td>
    </tr>
    <tr>
      <td>4</td>
      <td>Arrtourz / 2026</td>
      <td><strong>Quest Book Translator</strong></td>
      <td>
        <p>
          Traducerea textului din cărți în realitate mixtă
          (Meta Quest 3).
        </p>
      </td>
      <td>
        <p>Unity și C#.</p>
        <p>YOLO.</p>
        <p>Google Cloud Vision OCR.</p>
        <p>Google Cloud Translation API.</p>
      </td>
      <td>
        <p>Detectează continuu cărțile folosind YOLO local.</p>
        <p>Capturează imaginea la cererea utilizatorului.</p>
        <p>Extrage și traduce textul prin servicii cloud.</p>
        <p>Afișează traducerea într-un panou 3D ajustabil.</p>
      </td>
      <td>
        <p>Prototip funcțional demonstrat prin videoclipuri.</p>
        <p>Detectare locală în timp real.</p>
        <p>Captură la comandă.</p>
        <p>Traducere afișată în spațiul virtual.</p>
      </td>
      <td>
        <p>Necesită internet și servicii cloud cu posibile costuri.</p>
        <p>Traducerea nu suprascrie textul original.</p>
        <p>Sensibil la iluminare, focalizare și perspectivă.</p>
      </td>
      <td>
        <p>Proiect open-source experimental, destinat Meta Quest 3/3S.</p>
        <p>
          Propune ulterior OCR local prin PaddleOCR,
          reconstruirea aspectului textului
          și detectarea schimbării paginii.
        </p>
      </td>
    </tr>
    <tr>
      <td>5</td>
      <td>Mirela Domiciano / 2025</td>
      <td><strong>Image Pre-Processing Techniques for OCR</strong></td>
      <td>
        <p>Prelucrarea imaginilor digitale.</p>
        <p>Îmbunătățirea documentelor scanate sau fotografiate.</p>
        <p>Recunoașterea optică a caracterelor (OCR).</p>
      </td>
      <td>
        <p>OpenCV.</p>
        <p>Normalizare și redimensionare.</p>
        <p>Conversie în tonuri de gri.</p>
        <p>Binarizare adaptivă.</p>
        <p>CLAHE pentru îmbunătățirea contrastului.</p>
        <p>Filtre mediane și bilaterale pentru reducerea zgomotului.</p>
        <p>Transformări geometrice pentru corectarea perspectivei.</p>
      </td>
      <td>
        <p>
          Sunt analizate individual și în combinații
          cele șapte operații de preprocesare.
        </p>
      </td>
      <td>
        <p>
          Articolul propune evaluarea compromisului
          dintre viteza procesării și acuratețea extragerii textului.
        </p>
        <p>
          Sunt definite metrici precum latența,
          timpul de execuție, numărul de câmpuri extrase corect,
          procentul de potriviri corecte și eficiența globală.
        </p>
      </td>
      <td>
        <p>
          Set de testare redus, de numai cinci imagini,
          ceea ce limitează generalizarea rezultatelor.
        </p>
      </td>
      <td>
        <p>
          Sursă relevantă pentru proiectarea unui pipeline
          de preprocesare înainte de OCR.
        </p>
      </td>
    </tr>
    <tr>
      <td>6</td>
      <td>Nikolay Sapunov / 2026</td>
      <td><strong>PaddleOCR For Video - Text Detection Deep-Dive</strong></td>
      <td>
        <p>
          Procesarea imaginilor și Computer Vision,
          cu accent pe OCR în fluxuri video.
        </p>
      </td>
      <td>
        <p>PaddleOCR PP-OCRv5 și DBNet.</p>
        <p>Clasificator de orientare și SVTR_LCNet.</p>
        <p>OpenCV / FFmpeg.</p>
        <p>ONNX Runtime, OpenVINO și TensorRT.</p>
        <p>Tracking și agregare temporală.</p>
      </td>
      <td>
        <p>1. Text Detection: localizarea regiunilor cu text.</p>
        <p>2. Orientation Classification: corectarea orientării textului.</p>
        <p>3. Text Recognition: identificarea caracterelor și obținerea textului.</p>
      </td>
      <td>
        <p>
          Modelul mobile poate procesa un cadru 1080p
          în aproximativ 60–90 ms pe procesor.
        </p>
        <p>
          Varianta server: aproximativ 30–60 ms pe GPU,
          în condițiile de testare specificate.
        </p>
      </td>
      <td>
        <p>1. Motion blur cauzat de mișcarea camerei sau a obiectelor.</p>
        <p>2. Rezoluția scăzută afectează recunoașterea caracterelor.</p>
        <p>3. Procesarea fiecărui cadru poate suprasolicita CPU/GPU.</p>
        <p>4. Recunoașterea poate varia între cadre consecutive.</p>
      </td>
      <td>
        <p>
          OCR-ul pentru video trebuie tratat ca proces temporal,
          nu ca succesiune de imagini independente.
        </p>
      </td>
    </tr>
    <tr>
      <td>7</td>
      <td>Mikel Broström</td>
      <td>
        <strong>
          BoxMOT: Pluggable State-of-the-Art Multi-Object Tracking Modules
        </strong>
      </td>
      <td>
        <p>
          Computer Vision și Multi-Object Tracking (MOT):
          identificarea și urmărirea consecventă a obiectelor
          între cadre consecutive.
        </p>
      </td>
      <td>
        <p>Python și C++.</p>
        <p>PyTorch și NumPy.</p>
        <p>YOLO și Kalman Filter.</p>
        <p>ReID (Re-identification).</p>
      </td>
      <td>
        <p>1. Modelul de detecție localizează obiectele în fiecare cadru.</p>
        <p>2. Tracking-ul estimează pozițiile și asociază detecțiile.</p>
        <p>3. Sunt utilizate informații geometrice pentru asociere.</p>
        <p>4. Fiecare obiect primește un ID menținut între cadre.</p>
        <p>
          5. Pot fi configurați algoritmi precum ByteTrack,
          BoT-SORT, StrongSORT, DeepOCSORT și OccluBoost.
        </p>
      </td>
      <td>
        <p>
          Repository-ul prezintă rezultate comparative
          pe seturi de date standard, folosind metrici
          precum HOTA, MOTA și IDF1.
        </p>
        <p>
          Valorile raportate depind de setul de date
          și configurația evaluată.
        </p>
      </td>
      <td>
        <p>1. Nu este un sistem OCR și nu citește textul din imagini.</p>
        <p>2. Depinde de calitatea detecției obiectelor.</p>
        <p>3. Rezultatele depind de algoritm, model și parametri.</p>
      </td>
      <td>
        <p>
          BoxMOT permite urmărirea aceleiași regiuni de text
          în cadre succesive, atribuindu-i un ID
          și facilitând agregarea rezultatelor OCR.
        </p>
      </td>
    </tr>
  </tbody>
</table>

## Atribuții

Modulul `unity/` a început ca o clonă a [`Unity-PassthroughCameraApiSamples`](https://github.com/oculus-samples/Unity-PassthroughCameraApiSamples).

Licența originală și mențiunile privind drepturile de autor sunt păstrate în `unity/`.
