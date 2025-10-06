(ns ev3-client.robot
  (:require [clojure.core.async :as async :refer [go >! <! >!! chan close! thread]]
            [clojure.data.json :as json]
            [clojure.string :as string]
   )
  (:import (java.net Socket)
           (java.io BufferedReader InputStreamReader BufferedWriter OutputStreamWriter PrintWriter))
  )

(def STATE (atom {}))

(defn send-action [& actions]
  (let [conn (:conn @STATE)]
    (if (nil? conn)
      (throw (Exception. "No conexion a robot, usar (connect)"))
      (-> conn
          :ch
          (>!! (json/write-str actions))))))

(defn socket-channels [host port]
  (let [c-out (chan)] ;; messages sent to this chan -> will be written to remote
    (let [^Socket s (Socket. host port)
          in  (BufferedReader. (InputStreamReader. (.getInputStream s)))
          out (PrintWriter. (BufferedWriter. (OutputStreamWriter. (.getOutputStream s))))]
      (thread
        (try
          (loop []
            (let [line (.readLine in)]
              (when line
                (if (string/starts-with? line ";" )
                  (println (str "ERROR: " line))
                  (let [data (json/read-str line :key-fn keyword)]
                    (when (and (map? data) (nil? (:op data)))
                      (println data))))
                (recur))))
          (catch Exception e
            (prn (str "EXCEPTION READING: " e)))
          (finally
            (.close in)))
        (prn "Finished connection[IN]: " host ":" port))
      (thread
        (try
          (loop []
            (when-let [to-send (async/<!! c-out)]
              (.println out to-send)
              (.flush out)
              (recur)))
          (catch Exception _)
          (finally
            (.close out)
            (close! c-out)))
        (prn "Finished connection[OUT]: " host ":" port))
      {:in in :out out :ch c-out})))

(defn connect []
  (swap! STATE assoc-in [:conn]
             (socket-channels "192.168.1.204" 12345))
  (send-action {:op "audio" :audio "connected"}))

(defn stop-action [action]
  (send-action {:port :A :op "stop_action" :action action}
                {:port :D :op "stop_action" :action action}))

(defn turn [direction]
  (case direction
    :right (send-action {:port "A,D" :op "set_speed" :speed1 100 :speed2 100 }
                        {:port "A,D"  :op "run_to_rel_pos" :pos 190 :pos2 -190})

    :left (send-action {:port "A,D" :op "set_speed" :speed1 100 :speed2 100 }
                       {:port "A,D"  :op "run_to_rel_pos" :pos -190 :pos2 190})))

(defn fw [n]
  (send-action {:port "A,D" :op "set_speed" :speed1 100 :speed2 100 } {:port "A,D"  :op "run_to_rel_pos" :pos (* 500 n)}))
